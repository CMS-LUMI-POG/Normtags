#!/usr/bin/env python
import logging
import os
import subprocess
import argparse
import itertools
import tempfile
import pandas
import numpy
from matplotlib import transforms, pyplot, ticker


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

RATIOS_TOP_YLIMIT = 1.25
RATIOS_BOTTOM_YLIMIT = 0.75
LUMI_TOP_YLIMIT = 16000 #going up!
LUMI_BOTTOM_YLIMIT = 0

# default figure size in inches (NOTE: tuple)
FIGURE_SIZE = (14, 11)

# (Jonas): tight_layout would be way better, but it does not handle
# legends outside plots, so we have to do the following hacks -- adjusts:
# adjusts for figuresize depending on layout (also keeping in mind
# rotated xaxis ticks)
FIGURE_ADJUSTS_TWO_FAT_ROWS = {
    "top": 0.96, "left": 0.06, "right": 0.85, "bottom": 0.15, "hspace": 0.55}
FIGURE_ADJUSTS_TWO_FAT_ONE_SLIM_ROWS = {
    "top": 0.96, "left": 0.06, "right": 0.85, "bottom": 0.04, "hspace": 0.75}
XAXIS_TICKS_MAX = 40
SPECIAL_COLOR1 = "#FF0000"
BG_STRIPE_ALPHA = 0.1
BG_STRIPE_COLOR = "#0000FF"
COLORS = itertools.cycle([
    "#000000", "#00FF00", "#0000FF", "#01FFFE", "#FFA6FE", "#FFDB66",
    "#006401", "#010067", "#95003A", "#007DB5", "#FF00F6", "#774D00",
    "#90FB92", "#0076FF", "#D5FF00", "#FF937E", "#6A826C", "#FF029D",
    "#FE8900", "#7A4782", "#7E2DD2", "#85A900", "#FF0056", "#A42400",
    "#00AE7E", "#683D3B", "#BDC6FF", "#263400", "#BDD393", "#00B917",
    "#9E008E", "#001544", "#C28C9F", "#FF74A3", "#01D0FF", "#004754",
    "#E56FFE", "#788231", "#0E4CA1", "#91D0CB", "#BE9970", "#968AE8",
    "#BB8800", "#43002C", "#DEFF74", "#00FFC6", "#FFE502", "#620E00",
    "#008F9C", "#98FF52", "#7544B1", "#B500FF", "#00FF78", "#FF6E41",
    "#005F39", "#6B6882", "#5FAD4E", "#A75740", "#A5FFD2", "#FFB167",
    "#009BFF", "#E85EBE"])


def main():
    parser = predefined_arg_parser()
    log.info("parsing main arguments")
    args = parser.parse_args()
    if not args.normtags and not args.types:
        args.types = ["hfoc", "bcm1f", "pltzero", "online"]

    fig = pyplot.figure(figsize=FIGURE_SIZE)
    data = None
    if args.xing:
        plot = fig.add_subplot(111)
        data, bxd_cols, fill = get_bunch_data(args.run, args.fill, args.beams)
        make_bunch_plot(plot, data, bxd_cols, args.run, fill, args.threshold)
        fig.tight_layout()
    else:
        data, cols, fill = get_data(args.types, args.normtags,
                                    args.run, args.fill, args.beams)
        fig.subplots_adjust(**FIGURE_ADJUSTS_TWO_FAT_ROWS)
        rows = 2
        if args.correlate is not None:
            x = args.correlate[0]
            y = args.correlate[1]
            if x in cols and y in cols:
                corr_plot = fig.add_subplot(3, 1, 3)
                make_correlation_plot(corr_plot, data, x, y)
                rows = 3
                fig.subplots_adjust(**FIGURE_ADJUSTS_TWO_FAT_ONE_SLIM_ROWS)
            else:
                log.warning("no data for %s or/and %s: cannot make"
                            " correlation plot", x, y)
        avglumi_plot = fig.add_subplot(rows, 1, 1)
        make_avglumi_plot(avglumi_plot, data, cols, args.run, fill)
        ratios_plot = fig.add_subplot(rows, 1, 2)
        make_ratio_plot(ratios_plot, data, cols, args.run, fill)

    if args.outfile is not None:
        log.info("printing data to file %s", args.outfile)
        data.to_csv(args.outfile)

    log.info("asking pyplot to show the plots")
    pyplot.show()


def predefined_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r", dest="run", type=int, help="run number")
    parser.add_argument(
        "-f", dest="fill", type=int, help="fill number")
    parser.add_argument(
        "--types", dest="types", metavar="type", type=str, nargs="+",
        default=[], help="space delimited types. Default (if no normtags"
        " specified): hfoc bcm1f pltzero online")
    parser.add_argument(
        "--normtags", dest="normtags", metavar="normtag", type=str, nargs="+",
        default=[], help="space delimited normtags (file path also possible)")
    parser.add_argument(
        "--correlate", dest="correlate", type=str, nargs=2,
        help="x and y: two types (or normtags) for correlation plot")
    parser.add_argument(
        "-b", dest="beams", type=str, help="beam mode")
    parser.add_argument(
        "--xing", dest="xing", action='store_true',
        help="bx granurality (types and normtags are ignored)")
    parser.add_argument(
        "-o", dest="outfile", type=str, help="file to output data")
    parser.add_argument(
        "-t", dest="threshold", type=float, default=0.4,
        help="values < max*threshold are not included in plots (this option"
        " applies for bunch plots (--xing) only). Default: 0.4")
    return parser


def prepare_brilcalc_call_tpl(run, fill, beams):
    time_selection = []
    if run is not None:
        time_selection += ["-r", str(run)]
    if fill is not None:
        time_selection += ["-f", str(fill)]
    if not time_selection:
        raise ValueError("Either run or fill must by specified")
    f = tempfile.NamedTemporaryFile()
    log.debug("temp file name: %s", f.name)
    cmd = ["brilcalc", "lumi", "--byls", "-u", "hz/ub", "-o", f.name]
    cmd += time_selection
    if beams is not None:
        cmd += ["-b", beams]
    return cmd, f


int_before_colon = lambda value: int(value.split(":")[0])


# (Jonas) FIXME: get_data and get_bunch_data has too much of same code
def get_data(types, normtags, run=None, fill=None, beams=None):
    log.info("getting data")
    cmd_tpl, f = prepare_brilcalc_call_tpl(run, fill, beams)
    got_cols = []
    merged = None
    for request in types + normtags:
        cmd = list(cmd_tpl)
        if request in types:
            if (request != "online"):
                cmd += ["--type", request]
        elif request in normtags:
            cmd += ["--normtag", request]
            if os.path.isfile(request):
                log.info("normtag is file: %s", request)
                request = "normtag"

        log.debug("calling subprocess: %s", " ".join(cmd))
        # (Jonas) TODO: check return code
        ret_code = subprocess.call(cmd)
        if ret_code != 0:
            log.warning("subprocess returned with errors. skipping")
            continue
        data = pandas.read_csv(f.name, skiprows=1)
        data = data[:-3]
        if data.empty:
            log.warning("No data parsed for %s", request)
            continue
        got_cols.append(request)

        if fill is None:
            fill = data["#run:fill"].iloc[0].split(":")[1]
            log.info("fill number determined: %s", fill)

        data["delivered(hz/ub)"] = data["delivered(hz/ub)"].map(float)
        data.rename(columns={"delivered(hz/ub)": request}, inplace=True)
        data = data.loc[:, ("#run:fill", "ls", request)]

        if merged is None:
            merged = data
        else:
            merged = pandas.merge(merged, data, how="outer",
                                  on=["#run:fill", "ls"])

    # remove rows where "#run:fill" is corrupted
    merged = merged[merged["#run:fill"].str.contains(':')].copy()
    merged["ls"] = merged["ls"].map(int_before_colon)
    merged["#run:fill"] = merged["#run:fill"].map(int_before_colon)
    merged.rename(columns={"#run:fill": "run"}, inplace=True)
    log.info("sucessfully got data")
    return merged, got_cols, fill


def get_bunch_data(run=None, fill=None, beams=None):
    log.info("getting bunch (--xing) data")
    cmd, f = prepare_brilcalc_call_tpl(run, fill, beams)
    cmd += ["--xing"]
    log.debug("calling subprocess: %s", " ".join(cmd))
    # (Jonas) TODO: check return code
    subprocess.call(cmd)
    data = pandas.read_csv(f.name, skiprows=1)
    data = data[:-3]
    if data.empty:
        log.error("No data parsed")
        return None, None, None

    if fill is None:
        fill = data["#run:fill"].iloc[0].split(":")[1]
        log.info("fill number determined: %s", fill)

    # renaming ahead of time to make code lines shoreter :)
    data.rename(inplace=True, columns={
        "#run:fill": "run",
        "[bxidx bxdelivered(hz/ub) bxrecorded(hz/ub)]": "bunches"})
    data = data.loc[:, ("run", "ls", "bunches")]
    # remove rows where "#run:fill" is corrupted
    data = data[data["run"].str.contains(':')].copy()
    data["ls"] = data["ls"].map(int_before_colon)
    data["run"] = data["run"].map(int_before_colon)

    def bunches_to_columns(row):
        bunch_data = row["bunches"][1:-1].split(" ")
        cols = ["bxd:" + id for id in bunch_data[0::3]]
        delivereds = [float(delivered) for delivered in bunch_data[1::3]]
        return pandas.Series(data=delivereds, index=cols)

    split_bunches = data.apply(bunches_to_columns, axis=1)
    data.drop("bunches", axis=1, inplace=True)
    data = pandas.concat([data, split_bunches], axis=1)
    bxd_cols = data.columns.values.tolist()[2:]
    log.info("sucessfully got data")
    return data, bxd_cols, fill


def create_runls_ticks_formatter(dataframe):
    log.info("creating x axis ticks formatter")
    labels = ["{0:d}:{1:>4}".format(run, ls)
              for run, ls
              in zip(dataframe["run"], dataframe["ls"])]

    def runnr_lsnr_ticks(x, p):
        x = int(x)
        if x >= len(labels) or x < 0:
            return ""
        else:
            return labels[x]

    log.info("ticks formatter created")
    return ticker.FuncFormatter(runnr_lsnr_ticks)


def plot_by_columns(subplot, data, cols, special=None, legend=True):
    log.info("plotting by column")
    for col in cols:
        linestyle = "-"
        color = COLORS.next()
        if (col == special):
            color = SPECIAL_COLOR1
            linestyle = "--"

        log.debug("adding line for: %s", col)
        subplot.plot(data.index, data[col], linestyle=linestyle,
                     c=color, label=col)

    if legend:
        subplot.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    subplot.set_xlabel("RUN:LS")
    subplot.xaxis.set_major_formatter(create_runls_ticks_formatter(data))
    subplot.xaxis.set_major_locator(ticker.MaxNLocator(nbins=XAXIS_TICKS_MAX))
    subplot.xaxis.set_tick_params(labelsize=12)
    subplot.grid(True)
    # (Jonas): could not find more beautiful way to set axis labels rotation
    pyplot.setp(subplot.xaxis.get_majorticklabels(), rotation=90)


def separate_runs_on_plot(subplot, data):
    """
    put run number every run change, color background for every second run
    """
    log.info("visualizing run changes")
    # prepare transformation to treat x as data values and y as
    # relative plot position
    trans = transforms.blended_transform_factory(
        subplot.transData, subplot.transAxes)
    data.sort(["run", "ls"], inplace=True, ascending=[True, True])
    put_bg_switch = False
    for run_group in data.groupby("run"):
        runnr, data = run_group
        x = data.index[0]
        subplot.text(x, 0.99, s=runnr, ha="left", va="top",
                     rotation=90, transform=trans)
        if put_bg_switch:
            xmax = data.index[-1]
            subplot.axvspan(x, xmax, facecolor=BG_STRIPE_COLOR,
                            alpha=BG_STRIPE_ALPHA)

        put_bg_switch = not put_bg_switch


def calculate_ratios(data, cols):
    """Update DataFrame 'data' with ratios"""
    log.info("calculating ratios")
    # back up numpy settings and set to ignore all errors (to handle
    # "None"s and division by zero)
    old_numpy_settings = numpy.seterr(all="ignore")
    comparables = [x for x in cols if x != "online"]
    calculated_ratios = []
    for above_idx, above in enumerate(comparables):
        for below in comparables[above_idx + 1:]:
            name = above + "/" + below
            data[name] = data[above]/data[below]
            calculated_ratios.append(name)

    numpy.seterr(**old_numpy_settings)
    return calculated_ratios


def make_correlation_plot(plot, data, x, y):
    log.info("making correlation plot")
    plot.scatter(data[x], data[y]/data[x], alpha=0.5)
    log.info("calculating fit")
    # filter NaN's None's ...
    mask = numpy.isfinite(data[x]) & numpy.isfinite(data[y])
    k, c = numpy.polyfit(data[x][mask], (data[y]/data[x])[mask], 1)
    linex = [data[x].min(), data[x].max()]
    liney = [data[x].min()*k+c, data[x].max()*k+c]
    log.info("adding fit line")
    plot.plot(linex, liney, c=SPECIAL_COLOR1)
    text = r"$y(x)= x*{0} + ({1})$".format(k, c)
    plot.text(0.0, 1.0, s=text, ha="left", va="top",
              fontsize=16, transform=plot.transAxes)
    plot.set_xlabel(x)
    plot.set_ylabel("{0}/{1}".format(y, x))
    plot.set_title("Correlation")
    plot.grid(True)


def make_avglumi_plot(plot, data, cols, run, fill):
    log.info("making abglumi plot")
    plot_by_columns(plot, data, cols, "online")
    plot.set_ylabel("lumi (hz/ub)")
    ylims = plot.get_ylim()
    if ylims[0] < LUMI_BOTTOM_YLIMIT:
        plot.set_ylim(bottom=LUMI_BOTTOM_YLIMIT)
    if ylims[1] > LUMI_TOP_YLIMIT:
        plot.set_ylim(top=LUMI_TOP_YLIMIT)

    if run is None:
        plot.set_title("Fill {0}".format(fill))
        separate_runs_on_plot(plot, data)
    else:
        plot.set_title("Run {0}, Fill {1}".format(run, fill))


def make_ratio_plot(plot, data, cols, run, fill):
    ratios = calculate_ratios(data, cols)
    log.info("creating ratios plot")
    plot_by_columns(plot, data, ratios)
    plot.set_title("Lumi ratios")
    plot.set_ylabel("lumi ratios")
    ylims = plot.get_ylim()
    if ylims[0] < RATIOS_BOTTOM_YLIMIT:
        plot.set_ylim(bottom=RATIOS_BOTTOM_YLIMIT)
    if ylims[1] > RATIOS_TOP_YLIMIT:
        plot.set_ylim(top=RATIOS_TOP_YLIMIT)

    if run is None:
        separate_runs_on_plot(plot, data)


def make_bunch_plot(plot, data, cols, run, fill, threshold):

    def filter_by_percentage_of_max(row):
        max = row.max()
        row[row < max*threshold] = None
        return row

    data.iloc[:, 2:] = data.iloc[:, 2:].apply(
        filter_by_percentage_of_max, axis=1)

    log.info("creating plot")
    log.info("plotting by bunch")
    plot_by_columns(plot, data, cols, legend=False)
    plot.set_ylabel("bxdelivered (hz/ub)")

    if run is None:
        plot.set_title(
            "By bunch. Fill:{0}, threshold:{1}".format(fill, threshold))
        separate_runs_on_plot(plot, data)
    else:
        plot.set_title("By bunch. Run:{0}, Fill:{1}, threshold:{2}".format(
            run, fill, threshold))


if __name__ == "__main__":
    main()
