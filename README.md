# Table of Contents <!-- omit in toc -->
- [Guide on How To Make Video Clips from IVBSS or Safety Pilot](#guide-on-how-to-make-video-clips-from-ivbss-or-safety-pilot)
  - [IVBSS Videos](#ivbss-videos)
  - [Safety Pilot Videos](#safety-pilot-videos)
  - [Example #1 Calculation](#example-1-calculation)
  - [Example #2 Calculation](#example-2-calculation)
- [Coordinating Video and Kinematics Dataset](#coordinating-video-and-kinematics-dataset)

# Guide on How To Make Video Clips from IVBSS or Safety Pilot 

## IVBSS Videos
1. Locate IVBSS video on the UMTRI server based on driver-id, camera view and trip number.
Videos are located in the `\\tri-esgdb\DataE\IvbssLv\Fot` folder and marked as `.bin` files. You will need server access for this step. Videos are divided into folders by drivers. For example, Driver 2 and Trip Number 23 for the forward camera view can be found at:  
`\\tri-esgdb\DataE\IvbssLv\Fot\002\Video\Forward_002_0023.bin`

2. Use Mich Rasulis' `MakeAviFile.exe` custom program to convert this customized file to an AVI file (manual step). Obtain software from Mich directly (mich@umich.edu). You will need to install the software on a **Windows** machine. I installed it at the root folder `C:\`. The program will construct an AVI file from the individual frames in the file with the timestamp you specified in fps. You can convert individual files or a folder. Forward and face videos are **10 fps** while cabin, left, right videos are **2 fps**. You should verify the frame rate in step 3 below as a sanity check. Frame height and width are 240 and 720 respectively.

3. Query `{Cabin,Face,Forward,Left,Right}Index` table in `LvFot` database to find closest `VideoTime` to given timestamps (centiseconds). You can look at the difference between consecutive `VideoTime` to get an approximation of the frame rate. You will need server access for this step.

4. Find associated `{Cabin,Face,Forward,Left,Right}Count` (frame number).

5. Subtract offset (i.e. starting frame number which is not necessarily = 1) to get the frame number. 

6. Knowing the fps and the frame number, we can specify the appropriate timeframe in seconds as the offset frame number divided by frame rate for the `ffmpeg` command. You will need to have [ffmpeg](https://ffmpeg.org/) installed beforehand.

Use the `ffmpeg` command in the Command Prompt or Terminal to trim the video:

`ffmpeg -i <input-filename> -ss <starttime> -to <endtime> -c copy <output-filename>`

where 
- `starttime` = (frame number at start of window - frame number at start of trip)/fps
- `endtime` = (frame number at end of window - frame number at start of trip)/fps

## Safety Pilot Videos
Working with Safety Pilot is similar with the exception that the server where the data resides is different. The Safety Pilot videos are located at `\\tri-spfs3\DasData2\SP` for light vehicles and motorcycles and `\\tri-spfs4\DasData\SP` for heavy trucks and buses.

## Example #1 Calculation
**Objective**: Create a video clip that corresponds to driver=1, trip=20, and cabin camera view between the timestamps 50330 and 51580 centiseconds from the IVBSS dataset.

1. Select the file of interest. In this example, the file is located on the UMTRI server at  `\\tri-esgdb\DataE\IvbssLv\Fot\001\Video\Cabin_001_0020.bin`. Make sure file resides in a directory that is accessible by the `MakeAviFile.exe` program. Copy file if necessary.
2. Open the MakeAviFile program to convert the binary file. Select file/folder. Specify the frame rate and the frame height & width. Specify batch mode (or not). Specify filename name with `.avi` extension (not necessary for batch mode). Click `Create` button. This should create an AVI file that contains the entire trip.

![screenshot of software](https://github.com/caocscar/how-to-make-video-clips-ivbss-safetypilot/blob/master/makeavifile-software.png)

3. To trim the video to an arbitrary window, we use the software [ffmpeg](https://ffmpeg.org). But first, we need to look up the `CabinIndex` table on the UMTRI Server to get some additional information. Querying the driver/trip combination gives us the following results.

![screenshot of SQL query](https://github.com/caocscar/how-to-make-video-clips-ivbss-safetypilot/blob/master/cabinindex.png)

We can see that `50284` is the closest `VideoTime` before the start of the window and `51533` is the closest `VideoTime` before the end of the window. These correspond to `CabinCount` frames of `1004` and `1029` respectively. We see that the video starts at `CabinCount = 1` based on row 1 (this is not always the case though). `CabinCount` can be thought of as the frame number for the Cabin video.

4. Use the `ffmpeg` command in the Command Prompt or Terminal to trim the video:

`ffmpeg -i <input-filename> -ss <starttime> -to <endtime> -c copy <output-filename>`

where 
- `starttime` = (`CabinCount` at start of window - `CabinCount` at start of trip)/fps = (1004 - 1)/2 = 501.5
- `endtime` = (`CabinCount` at end of window - `CabinCount` at start of trip)/fps = (1029 - 1)/2 = 514.0

This results in the command:

`ffmpeg -i Cabin_001_0020.avi -ss 501.5 -to 514 -c copy Cabin_001_0020_trimmed.avi`

Done!

## Example #2 Calculation
**Objective**: Create a video clip that corresponds to driver=1, trip=20, and face camera view between the timestamps 50330 and 51580 centiseconds from the IVBSS dataset.

1. Select the file of interest. In this example, the file is located on the UMTRI server at 
`\\tri-esgdb\DataE\IvbssLv\Fot\001\Video\Face_001_0020.bin`.

2. Create the AVI video at a frame rate of 10 fps.

3. We need to look up the `FaceIndex` table on the UMTRI Server to get some additional information. Querying the driver/trip combination gives us the following results.

![screenshot of SQL query](https://github.com/caocscar/how-to-make-video-clips-ivbss-safetypilot/blob/master/faceindex.png)

We can see that `50317` is the closest `VideoTime` before the start of the window and `51574` is the closest `VideoTime` before the end of the window. These correspond to `FaceCount` frames of `5027` and `5152` respectively. We see that the video starts at `FaceCount = 7` based on row 1. `FaceCount` can be thought of as the frame number for the Face video.

4. Use the `ffmpeg` command in the Command Prompt or Terminal to trim the video:

`ffmpeg -i <input-filename> -ss <starttime> -to <endtime> -c copy <output-filename>`

where 
- `starttime` = (`FaceCount` at start of window - `FaceCount` at start of trip)/fps = (5027 - 7)/10 = 502.0
- `endtime` = (`FaceCount` at end of window - `FaceCount` at start of trip)/fps = (5152 - 7)/10 = 514.5

This results in the command:

`ffmpeg -i Face_001_0020.avi -ss 502 -to 514.5 -c copy Face_001_0020_trimmed.avi`

**Note**: Notice how the times for the two examples are very similar even though the frame numbers are very different for the two camera views.


<hr>

# Coordinating Video and Kinematics Dataset
The script `regression_models.py` is an example script I used to create a mapping between the time columns in Safety Pilot between video frames `VideoTime` (centiseconds since start of the trip) and the kinematics data `Gentime` (number of microseconds since Jan 1, 2004 (UTC +00:00)). 
