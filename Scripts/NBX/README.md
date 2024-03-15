This directory contains some more details on the number of bunches calculation. `getNBX.py` uses four sources of information to determine the total number of bunches in the fill:
* the "target" number of bunches from WBM, which is derived from the published filling scheme
* the "colliding" number of bunches from WBM, which is derived from some (not entirely known to me) combination of the beam information and the luminometer data
* the "ncollidingbx" number from the brilcalc beam data (`brilcalc beam -f FILL`)
* the actual number of bunches observed in the luminometers (hfoc and pltzero for 2015 and 2016, hfet and pltzero for 2017)

Ideally these should all agree, of course, but in practice there are some differences. The .csv files in the parent directory contain the final authoritative number (usually derived from the luminometer data). This directory contains some tools for figuring out how to get to the correct number from the starting output of `getNBX.py`.

## Files

* `2015FillsWBM.csv`, `2016FillsWBM.csv`, `2017FillsWBM.csv`, and `2018FillsWBM.csv` contain all of the 2015, 2016, 2017, and 2018 fill data from WBM. A few fills have been removed:
  * (2015) Fill 3599 was a very early test of the Stable Beams flag but this was well before actual beams were present or BRILDAQ was taking data, so there is no luminometer data for this fill.
  * (2015) Fill 4717 is in WBM as a fill with Stable Beams, but there is no actual data for this fill present either in WBM or in the lumi DB. Possibly this was also a test of some sort.
  * (2017) Fill 5659 is also a test of the Stable Beams flag but with no actual data.
  * (2018) Fill 6469 is also a test of the Stable Beams flag with no actual collisions.

* `results_2015_final.txt`, `results_2016_final.txt`, `results_2017_final.txt`, and `results_2018.txt` contain the final output from `getNBX.py`. This is after the thresholds for some fills have been manually adjusted and some discrepancies have been manually resolved. There are still some mismatches in this output caused by, for instance, HI fills where some bunches fluctuate above or below the threshold, but these mismatches are relatively uncommon. The remaining discrepancies are discussed in more detail below. The file contains one line for each fill, of the format:
fill number,WBM target bunches,WBM colliding bunches,beam bunches,luminometer bunches
as well as various informational and error messages; if you just want the output data, you can grep for lines containing ",".

* `investigateBeamDiffs.py` is a script to further investigate cases where the beam data differs from the luminometer data. It will go through the per-BX per-LS beam data and look for differences. Run it with one or more fill numbers as arguments to investigate those fills.

* `investigateBXLumiDiffs.py` is a script to further investigate cases where the luminometer per-BX data disagrees between the luminometers. As above, run it with one or more fill numbers as arguments.

* `postprocess.py` takes the final output file, and breaks the fills down into different categories depending on whether all four inputs agree, or whether one (or more) inputs disagree with the rest. It will also look for fills which have been affected by the TCDS bug which causes the number from the beam data to be off by one (this categorization is orthogonal to the above, so a fill may appear in both this category and one other category). It will also write out a final CSV file.

## 2015 details

Here's a more detailed breakdown of the fills where we don't see perfect agreement with the four individual sources:

* Fills 4212, 4214, 4219, 4220, 4224, 4225, and 4231: In these fills, due to problems with emittance blowup, BX 1 has a very low luminosity (<1% of the regular colliding bunches). Consequently it appears in the WBM target count and the beam count, but not in the WBM colliding count or the luminometer count. (Whether or not you actually want to include this bunch in your count will probably depend on your individual use case.) In all of these fills except 4219, the bunch has a low enough intensity that it doesn't appear in the per-BX beam data, either, so the count using `investigateBeamDiffs.py` is consistent with the luminometer count; in 4219 it appears at the beginning of the fill but drops below the threshold soon after.
* Fills 4659 and 4661: These fills have the opposite issue. In the filling scheme used for these fills BX 1 has a low intensity in beam 1, so it is not counted in the WBM target count or the beam count. However, these bunches still produced significant luminosity (about half of the regular colliding bunches), so they are counted in the WBM colliding count and luminometer count. They should probably be counted as colliding bunches in these fills.
* Fill 4706: In this fill there were apparently problems with the beam 1 intensity measurement at the beginning of the fill, so only 422 out of the 424 bunches present are correctly counted in the WBM count. These appear to be fixed mid-fill, so if you look at the per-LS per-BX beam data (with `brilcalc beam --xing -f FILL`) you can see it becomes correct. (The "ncollidingbx" count has already been fixed to include all 424 bunches.) The luminometers correctly report 424 bunches (in agreement with the filling scheme) throughout the fill.
* Fill 3855: In this very early 2015 fill, the filling scheme and the "ncollidingbx" count both report 37 colliding bunches. However, looking at the actual beam intensity as above, there are only 29 colliding bunches, which is consistent with the luminometer count as well.
* Fills 4008, 4513, 4691, 4692, 4693, 4695, 4696, 4697, 4698, 4699, and 4709: In these fills the "WBM target" number is incorrect but the other three are consistent. In all cases this simply seems to be a case where the filling scheme was incorrectly parsed by WBM; the actual number of colliding bunches as specified in the filling scheme does agree with the number of colliding bunches observed.
* Fills 3819, 3820, 3824, 3829, 3835, 3846, 3847, 3848, 3850, 3851, 3855, 3857, 3858, 4266, and 4440: In these fills the "WBM colliding" number is zero while the other three sources have the correct number (except for 3855 discussed above). This is most likely because the threshold in WBM was set too high for these fills with low luminosity, so the colliding bunches were missed. The correct count from the other three sources is used.
* Fills 4337, 4418, 4420, 4423, 4426, 4428, 4432, 4434, 4435, 4437, 4444, 4448, 4710, 4711, 4719, and 4720: These are similar to the above but in these fills the "WBM colliding" number is only off by a few bunches relative to the other three. These are also likely due to the thresholds being slightly off and thus a few lower luminosity bunches are missed in the WBM count. Again, the count from the other three sources is used.
* Fills 3965, 4207, 4211, and 4246: In these cases the "WBM colliding" number is high by a few bunches relative to the other three; in this case this is presumably due to the threshold being a little too low and thus picking up a few bunches which do not actually contain collisions (possibly due to high background rates in these bunches for whatever reason).

Here's some notes on the various tweaks to `getNBX.py` required to get best results for the luminometer bunch computation:

* For the 2015 PbPb fills (4658-4720), I got best results by increasing the threshold for HFOC to 0.15 and decreasing it for PLT to 0.05. There are still some fills where the number of bunches above threshold does not remain stable so you see a few mismatches in the output.
* Fill 4689: This is the VdM scan fill during PbPb running, so for HFOC it is basically impossible to set a single threshold without either some extra bunches ending up above the threshold or some real bunches falling below the threshold. This fill has been manually excluded for HFOC in `getNBX.py`.
* Fills 4499, 4505, 4509, 4510, and 4511: In these fills there are three noncolliding bunches (1767, 1771, and 1775) which consistently show up in PLT as producing nonnegligible luminosity (maybe the background in these bunches was high for some reason). Thus the PLT will consistently come out higher than the true count. (In HFOC you can also see BX 1767 appear sometimes in fill 4510.) These fills have been manually excluded for PLT in `getNBX.py`. Fill 4499 also has the additional difficulty that it is very low luminosity so the normal --xingTr flag doesn't work well to find bunches above threshold. Instead, try using --xingMin 0.0025.
* Fill 4243 is affected by the same blowup issues as in 4212-4231 but not as severely. At the beginning of the fill, it's about half the luminosity of the regular bunches, but by the end, it's down to about 5%, so you need to lower the threshold a bit or otherwise it will seem to disappear.
* Fills 4210 and 4211 are also similar to 4243: BX 1 is visible at the beginning of the fill but decays much more rapidly and disappears by the end of the fill.
* Fills 3846, 3847, 3848, 3850, 3851, 3960, 3962, and 3965: For these fills there is no HFOC data available, so I used BCM1F as the other luminometer for comparison.
* Fills 3848, 3960, 3962, 3965, 3971, 3974, 3976, 4322, and 4323: In these fills the PLT timing is incorrect so the two halves of the PLT are out of sync by one BX, so the luminosity from a single bunch is split into two bunches, so the bunch count from PLT will be incorrect. These fills have been manually excluded for PLT in `getNBX.py`.
* Fills 4207, 4208, 4210, 4211, 4212, and 4214: In these fills the PLT timing is incorrect as above and the overall BX alignment is shifted (which doesn't actually affect the count of number of bunches, but makes it more difficult to identify the source of the problem). As above, these fills have been manually excluded for PLT in `getNBX.py`.
* Fill 3992: In this fill HFOC is affected by a similar problem, in that the luminosity of a single bunch is split into two adjacent BXes in the output. This fill has been manually excluded for HFOC in `getNBX.py`.
* Fills 3846 and 3847: These are possibly the most difficult fills of all. These are very early 2015 fills with very low luminosity. HFOC data is not available at all for these fills, and PLT has the problem that the background spillover into the next BX is of the same magnitude as the actual luminosity. The BCM1F data is usable, but because of the very low luminosity, even colliding bunches can have zero luminosity for an entire LS. As a result, instead of using the normal method of determining filled BXes, I added an alternate method to `getNBX.py` which combines a number of lumisections and looks for any bunches which report luminosity in this time. This gives a filled bunch pattern which agrees with the nominal filling scheme. This mode can be activated using the `veryLowFills` option in `getNBX.py`.

## 2016 details

The 2016 data is (thankfully) much cleaner than the 2015 data, but there are still a few fills which show disagreement:

* Fill 4890: This fill includes 49 regular colliding bunches but also one pilot bunch (BX 969). This bunch has a little less than 10% the intensity of a regular bunch and so less than 1% of the luminosity of a regular bunch. As a result, it is not counted in the WBM target count or the luminometer count, but it does appear in the WBM colliding count and the beam count. Whether or not you want to count this bunch probably depends on your application.
* Fills 5149 and 5151: In these fills the filling scheme listed in WBM is incorrect, so the target number of bunches in WBM is naturally also incorrect. The correct filling scheme agrees with the number of bunches actually observed in these fills.
* Fills 4960, 4961, 4964, and 5370: In these fills the WBM target number appears to have parsed the filling scheme incorrectly, as the number of bunches specified in the filling scheme does not agree with the WBM target number. The number of bunches in the filling scheme does agree with the observed number of bunches, so it's just the WBM target number which is in error.
* Fills 5038, 5205, and 5418: In these fills the number of colliding bunches is less than the number of bunches specified in the filling scheme. This is because the fill for beam 2 could not be completed because the heat limits of the LHC were reached.
* A large number of fills are affected by a bug in TCDS which causes the beam data to show one fewer colliding bunch than actually present. Here's the full list: 4915, 4919, 4924, 4925, 4926, 4930, 4935, 4942, 4947, 4953, 4956, 4958, 4960, 4961, 4964, 4965, 4976, 4979, 4980, 4984, 4985, 4988, 4990, 5005, 5013, 5017, 5020, 5021, 5024, 5026, 5027, 5028, 5029, 5030, 5038, 5183, 5187, 5196, 5197, 5198, 5199, 5205, 5206, 5209, 5210, 5211, 5213, 5219, 5222, 5223, 5229, 5251, 5253, 5254, 5256, 5257, 5258, 5261, 5264, 5265, 5266, 5267, 5270, 5274, 5275, 5276, 5277, 5279, 5282, 5287, 5288, 5338, 5339, 5340, 5345, 5351, 5352, 5355, 5391, 5393, 5394, 5395, 5401, 5405, 5406, 5416, 5418, 5421, 5423, 5424, 5426, 5427, 5433, 5437, 5439, 5441, 5442, 5443, 5446, 5448, 5450, 5451.

The 2016 data also requires less tweaking of thresholds in `getNBX.py` than the 2015 data, but for early fills (less than 5000 or so) it is recommended that you raise the threshold for hfoc to 0.3 or so for best results.

## 2017 details

The 2017 data is also pretty clean. Here's the remaining fills which show disagreement:

* The filling scheme in fill 6385 specifies 1824 colliding bunches, while the luminometers and beam data both report 1828 colliding bunches. Looking at the LHC OP elog for this fill, it looks like the first train in beam 1 was indeed shifted during injection, which brought 4 bunches in that train into collision with beam 2, so the luminometer numbers are correct.
* For fills <= 5837, there is a lot of instability in the HFET measurement of the number of bunches. For simply measuring the number of bunches with `getNBX.py` this is probably not a problem but for more detailed studies you are probably better off using HFOC instead.
* The following fills have an incorrect number of colliding bunches shown in WBM: 6386, 6239, 6238, 6236, 6230, 6194, 6192, 6191, 6185, 6180, 6177, 6176, 6175, 6165, 6161, 6160, 6159, 6155, 6152, 6147, 6146, 6143, 6142, 6140, 6138, 6119, 6116, 6106, 6105, 6104, 6098, 6097, 6093, 6090, 6089, 6082, 6061, 6060, 6057, 6054, 6053, 6052, 6050, 6048, 6046, 6044, 6041, 6031, 6021, 6018, 6015, 6012, 5980, 5976, 5966, 5965, 5962, 5960, 5946, 5942

  For all fills except the specific cases below, the number of colliding bunches is off by 1 relative to the correct number of bunches, as verified from the beam data, luminometer data, and target number of bunches. It's not clear to me where this error comes from, since the WBM BunchFill shows the correct number of bunches in all cases (except for 6012 and 6015, which are very low luminosity VdM fills, so the BunchFill shows zero colliding bunches). The exceptions: fill 6061 is off by two instead of 1, and fills 6230, 6236, 6238, and 6239 appear to have no beam or luminosity data at all in WBM, so the number of colliding bunches in WBM is 0. I have contacted the WBM team so that they could fix this, but have heard no response as of yet.
* All of the fills affected by the TCDS off-by-one bug in the beam data have been fixed (see below for details).

### Shifts in BX data

In addition, for 2017, I did a detailed study to verify that not only the number of bunches was accurate, but also that the beam patterns themselves matched. This uncovered a few problems, most of which were fixed (see below), but a couple were not simply fixable and so are noted here:

* Fill 6385: In this fill (for the entire fill) the pltzero data is shifted in exactly ONE place: the bunch that should be BX 16 is in fact in BX 17. I have no idea what could cause this. As mentioned above, the filling scheme was changed during injection (and this bunch is one of the affected bunches) so perhaps the timing of this bunch was abnormal.
* Fill 5883: In this fill, for the period from the beginning of the fill to 297670:31, there is again a single-bunch displacement, in that the bunch that should be BX 2088 is atually in BX 2087. This period was affected by TCDS issues which caused a shift in the data; the shift has been fixed but it is possible that the shift was not actually an integral number of BXs and so this bunch was affected differently.

### Fixes applied

Some of the data was fixed after initial studies:

* These fills were affected by a bug in the TCDS ncollidingbx measurement which caused the "brilcalc beam" number to be 1 low:
6392, 6390, 6389, 6388, 6387, 6386, 6385, 6384, 6382, 6272, 6271, 6269, 6268, 6266, 6263, 6262, 6261, 6259, 6258, 6255, 6253, 6252, 6247, 6245, 6243, 6241, 6240, 6193, 6192, 6189, 6186, 6185, 6182, 6180, 6179, 6177, 6176, 6175, 6174, 6171, 6170, 6169, 6168, 6167, 6165, 6161, 6160, 6159, 6158, 6156, 6155, 6152, 6147, 6146, 6143, 6142, 6141, 6140, 6138, 6136, 6123, 6116, 6114, 6110, 6106, 6105, 6104, 6098, 6097, 6096, 6094, 6093, 6091, 6090, 6089, 6086, 6084, 6082, 6061, 6060, 6057, 6055, 6054, 6053, 6052, 6050, 6048, 6046, 6044, 6041, 6035, 6031, 6030, 6026, 6024, 6021, 6020, 5984, 5980, 5979, 5976, 5974, 5971, 5966, 5965, 5963, 5962, 5960, 5958, 5954, 5952, 5950, 5887, 5885, 5883, 5882, 5880, 5878, 5876, 5873, 5872, 5870, 5868, 5865, 5864, 5862, 5856, 5849, 5848, 5845, 5842, 5830, 5825, 5737, 5730.

  Fill 6119 was also wrong in this measurement (1631 vs. 1728). In all cases, looking at the full per-BX beam data gave the correct number of colliding bunches. This has now been fixed (in JIRA ticket [CMSBRIL-148](https://its.cern.ch/jira/browse/CMSBRIL-148)) and "brilcalc beam" returns the correct number now.

* All fills <= 5834 (i.e., 5698, 5699, 5704, 5710, 5717, 5718, 5719, 5722, 5730, 5737, 5746, 5749, 5750, 5822, 5824, 5825, 5830, 5833, 5834) were shifted in HFET by -1 BX for all bunches. These have now been fixed (JIRA ticket [CMSBRIL-149](https://its.cern.ch/jira/browse/CMSBRIL-149)) and HFET has the correct bunch pattern.

* In four fills, PLT was affected by TCDS issues which caused a shift in the data:
  * fill 5698, data from 294947:6 to the end of the fill was shifted by -828 BX.
  * fill 5839, data from 297050:8-69 was shifted by -827 BX.
  * fill 5883, data from the beginning of the fill to 297670:31 was shifted by -2071 BX.
  * fill 6364, data from 306155:1508-306169:2 was shifted by -188 BX.

  These have all been fixed now (same ticket as above). There are a few lumisections which can't be recovered by a simple shift (297050:6 in fill 5839, and 306155:1505-1507 in fill 5883) and so these were marked bad for PLT. In addition there remains one bunch in fill 5883 that is shifted, as described above.

## 2018 details

Here's fills for which some manual adjustments are necessary for the bunch measurement to work properly in 2018.

* Fill 6584 has no filling scheme in WBM (or on the LPC page) but it appears to be the same scheme as the preceding two fills, namely 25ns_75b_62_32_62_12bpi_9inj, so that has been fixed in the csv.

* In many fills, there is a spurious luminosity that appears in both HFET and HFOC due to the HF laser. In HFET it's generally confined to BX 3490, while in HFOC it spreads to the two neighboring BXes as well (and sometimes even BX 3492). In normal physics conditions, this is much smaller than real colliding bunches, so it does not pose a problem. However, in lower-luminosity fills, this can create a few problems:
  * In fills 6638, 6654, 6714, and 6925, this simply appears as an extra bunch somewhat below the colliding bunches, so it can be eliminated by increasing the threshold slightly.
  * In fills 6864, 6877, and 6884, the luminosity of the spurious bunch is greater than that of the real colliding bunches, so I excluded HFET from these fills, after verifying that this was the only difference between HFET and PLT.
  * In fills 6879, 6881, 6885, 6890, 6892, 7299, and 7406, the luminosity of the spurious bunch is so much greater than that of the real colliding bunches that some or all of them start falling below threshold. This is fortunately less of a problem in HFOC than HFET, so I compared HFOC to PLT, verified that the only differences were in 3490 (or neighbors), and then proceeded to exclude HF from these fills. In fills 6890 and 6892, there's an additional complication that one bunch, BX 16, has a much lower luminosity in the PLT measurement for some reason, causing it to be below threshold; the other luminometers show this bunch with having comparable luminosity to the other bunches, so I'm not sure why this happened in PLT; maybe some weird timing effect. (This is also true for fill 6891 but there the HFOC measurement is OK.) So for these fills I substituted BCM1F for PLT to make sure we had at least one reliable measurement. In fill 7299, the luminosity is so low that PLT doesn't always have hits in each bunch in each lumi section, so I used the alternate way of aggregating measurements over many lumisections to confirm the total count.
  * In fills 7300 and 7407, while HFET has the problems above, the first few lumisections of HFOC are free of the spurious luminosity from the laser, so we can just use HFOC instead and get consistent results. (Fill 7300, like fill 7299, is so low that we need to aggregate luminosity for the PLT to confirm that it agrees.)
  * Many of the HI fills (7427-7492) also have this problem, but since PLT is used as the primary luminometer for the BX determination for these fills, it doesn't create a problem with the final measurement.
    
* Fill 6699 has 9 real colliding bunches and 1 pilot bunch (in bunch 801). The pilot bunch is counted in the beam count but doesn't produce appreciable luminosity, so for most use cases it is correct to consider this with 9 bunches. (Note that HF has a spurious bunch in 3490, like above, so it also appears to have 10 colliding bunches, but as above, this count is definitely not correct.)

* Fills 6740 and 7447 were dumped as they went into STABLE BEAMS, so the bunches are already dying off in the first LS of stable beams. For these fills, I just used the data during ADJUST and manually removed the lumisections before reaching collision luminosity, at which point everything agrees well. (Fill 7447 does have the HF laser, however.)

* In fill 6847, BX 17 is consistently missing in the PLT data, and not just because it's slightly below threshold; it's basically near zero throughout the fill, despite the fact that according to HF it's one of the highest-luminosity bunches in the fill. This was noted at the time (http://cmsonline.cern.ch/cms-elog/1049667), but observed as a shift to the adjacent BX, while the data in the lumi DB does not show that. I have no idea what happened to cause this, but it doesn't affect the number of bunches measurement, since the HFET measurement is consistent.

* Fill 6882 is a low-luminosity fill that has some bunches flickering near the threshold in HFET (not the HF laser problem above, however). Raising the threshold slightly gives us consistent numbers.

* Fill 6966 has no data in the lumiDB at all (possibly because this was a machine development fill, albeit one with stable beams). However, from the online information stored in WBM, it looks like the beam and luminosity data is consistent with the nominal total of 12 colliding bunches. (The WBM target value is 0 because it looks like this special filling scheme was not parsed correctly.)

* In fill 7006, WBM lists a target of 2544 colliding bunches (which matches the filling scheme) but it looks like there were only 2400 colliding bunches in the fill. Looking at the LHC OP elog, it looks like the last injection in B1 was skipped due to RF issues, which accounts for the difference.

* In fills 7017 and 7018, the WBM colliding bunches number is slightly off from the target number (2541 and 2546 respectively, for a target of 2544). This appears to be due to threshold issues since there are a few bunches with lower intensity, but the actual collision data is consistent with 2544 bunches.

* In fill 7043, there were two bunches that are the last in their trains (869 and 1436) which have a much lower intensity in Beam 1 than normal, resulting in a significantly lower luminosity in these bunches. We can lower the threshold to pick these up, but then this also picks up bunch 3490 in HF (as above), so I verified that that was the only difference and then excluded HF. Note that the beam measurement also doesn't include these two bunches.

* Fill 7188, like fill 6966, is a MD fill with stable beams and has no data in the lumiDB. The online data in WBM shows no appreciable luminosity -- it's hard to tell if this is because the luminosity is very low or for some other reason -- but from the beam data, it looks like there are indeed 3 nominal colliding bunches. (Confusingly, the name of the filling scheme implies that there are only two colliding bunches, but looking at the filling scheme itself shows clearly that there are three, BX 1, 101, and 1886, which agrees with what the WBM beam data has.)

* In fill 7433, the PLT bunch luminosity is bad for about the first quarter of the fill, being spread across a large number of bunches. When I remove this section manually, then the PLT number of bunches agrees with the expected number. (HF still has the extra bunches in BX 3490 and neighbors.)

* Fills 7441, 7453, and 7492 have the same issues as above, except that there's no point where the PLT luminosity becomes good, so instead I substituted BCM1F. Fill 7492 also has the issue that although the declared filling scheme includes 733 target bunches, it looks like the injection was only partially completed for whatever reason, so there are only atually 271 colliding bunches.

* For fills 7464 and 7486, I had to lower the threshold for HFOC to pick up all of the bunches. (During the HI period there are also times in other fills where some bunches go briefly below threshold, but not enough to cause any issues.)

* In fill 7466, it looks like WBM has misparsed the filling scheme, as WBM lists 733 target bunches, but the filling scheme only calls for 670 colliding (which matches what's actually seen in the data).

* Fill 7475 has several issues that had to be fixed in order to get a good measurement of the number of bunches. First, although stable beams were declared in run 372308 LS 5, the fill doesn't reach peak luminosity until much later, in run 327310 LS 4, and before then the luminosity is too low to get a reliable measurement of the number of bunches. This was fixed by manually removing the lines for the first part of the fill from the brilcalc output. Second, the HFOC threshold had to be lowered slightly to pick up all the bunches. Finally, the PLT data appears to be shifted with respect to the nominal; a shift of 253 BX needs to be applied to recover the correct pattern. Once all of these are done, then everything looks correct.

### Fixes applied

Like 2017, there were some fills that had an inaccurate number of colliding bunches in the beam measurement. These have now been fixed (JIRA ticket [CMSBRIL-233](https://its.cern.ch/jira/browse/CMSBRIL-233) and hae been verified to be correct now.

* The following fills were off by one in the beam measurement, presumably also due to the TCDS issue: 7334, 7333, 7331, 7328, 7324, 7321, 7320, 7317, 7315, 7314, 7310, 7309, 7308, 7274, 7271, 7270, 7266, 7265, 7264, 7259, 7256, 7253, 7252, 7245, 7242, 7240, 7239, 7236, 7234, 7221, 7218, 7217, 7212, 7145, 7144, 7142, 7139, 7137, 7135, 7133, 7132, 7131, 7128, 7127, 7125, 7124, 7123, 7122, 7120, 7118, 7117, 7114, 7112, 7110, 7109, 7108, 7105, 7101, 7099, 7098, 7097, 7095, 7092, 7091, 7090, 7088, 7087, 7083, 7080, 7078, 7069, 7065, 7063, 7061, 7058, 7056, 7055, 7054, 7053, 7052, 7048, 7047, 7045, 7042, 7040, 7039, 7037, 7035, 7033, 7031, 7026, 7024, 7020, 7018, 7017, 7013, 7008, 7006, 6961, 6960, 6957, 6956, 6953, 6946, 6944, 6942, 6940, 6931, 6927, 6925, 6924, 6923, 6921, 6919, 6912, 6911, 6909, 6904, 6892, 6891, 6890, 6877, 6874, 6860, 6850, 6778, 6776, 6774, 6773, 6772, 6770, 6768, 6763, 6762, 6761, 6759, 6757, 6755, 6752, 6751, 6749, 6744, 6741, 6740, 6738, 6737, 6733, 6731, 6729, 6724, 6719, 6714, 6712, 6711, 6710, 6709, 6702, 6700, 6696, 6694, 6693, 6692, 6683, 6681, 6677, 6675, 6674, 6672, 6666, 6663, 6662, 6659, 6654, 6650, 6648, 6646, 6645, 6643, 6642, 6641, 6640, 6639, 6638, 6636, 6633, 6629, 6628, 6616, 6614, 6613, 6612

* Fill 7043 was off by three, presumably one because of the TCDS issue and two because of the beam issues mentioned above.

### Issues to be fixed

A ticket has been filed for these shifts.

* The following fills have shifts in a luminometer:
  * In fills 7211, 7212, and 7213, HFOC and HFET both need to be shifted by -1 BX.
  * In fills 7259, 7264, 7265, 7266, and 7270, only HFOC needs to be shifted by -1 BX.
  * In fill 7475, PLT needs to be shifted by 253 BX.
