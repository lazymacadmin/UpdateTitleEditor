> ⛔️ ATTENTION <br/>
> I am no longer maintaining this project because I no longer use/have access to the resources to maintain it.<br/>
> I have [asked](https://lazymacadmin.github.io/2024/02/14/so-long-farewell-goodbye.html#:~:text=I’m%20also%20looking%20to%20leave,wants%20to%20take%20it%20over.) [before](https://lazymacadmin.github.io/2024/10/08/updated-autopkg-teams-workflows.html#:~:text=I’m%20still%20looking%20to%20leave,wants%20to%20take%20it%20over.) for someone to maintain this project, but no one has stepped forward. As such, this project, while functional as of January 28, 2025, should be considered abandoned in its current form.
>

----------------------

# Processors To Do Stuff Easier   
I wrote/adapted these to make it easier to work with recipes in my Jamf instance. They work well for me but may take some work to fit into your workflows. I tried to require a minumum of extras to run these but didn't have the time to dedicate to removing all dependencies.  
  
[UpdateTitleEditor](https://github.com/lazymacadmin/UpdateTitleEditor#updatetitleeditorpy)  
[JamfClearPatchNotifications](https://github.com/lazymacadmin/UpdateTitleEditor#jamfclearpatchnotificationspy)  
[MistDownloader](https://github.com/lazymacadmin/UpdateTitleEditor#mistdownloaderpy)  
[JamfPatchTitleVersioner](https://github.com/lazymacadmin/UpdateTitleEditor#jamfpatchtitleversionerpy)  
[SleepIf](https://github.com/lazymacadmin/UpdateTitleEditor#sleepifpy)  


## UpdateTitleEditor.py
Autopkg processor to update Jamf's Title Editor

To use, you will need to add 3 entries to your autopkg config:
```
defaults write com.github.autopkg TITLE_URL https://your.title.url 
defaults write com.github.autopkg TITLE_USER title-editor-user
defaults write com.github.autopkg TITLE_PASS "title-editor-pass"
```
- As written you will also need to know the ***numeric*** ID of each title from Title Editor and use it as an input in each recipe as shown circled in red.<br/> ![Image of the Title Editor URL](Images/TitleEditorId.png)
- Make sure not to use a trailing slash on your Title Editor URL as shown:<br/> ![Title Editor Url](Images/TitleEditorUrl.png)

- There is a debug option to ensure you are getting the responses you expect. Run your recipe with `--key debug=true`

Feel free to run with this so I'm not stuck answering questions and/or trying to improve it any further.


## JamfClearPatchNotifications.py
Autopkg processor to clear notifications for new patch versions in Jamf Pro

To use you will need your autopkg install to have access to the requests module:
```
/Library/AutoPkg/Python3/Python.framework/Versions/Current/bin/pip3 install requests
```
Arguments needed in your autopkg recipes:
- patch_name: to match the patch title in Jamf Pro
- version: should be set in your autopkg recipe but can be over-ridden manually


## MistDownloader.py
Downloads macOS installers using [mist](https://github.com/ninxsoft/mist-cli) - must be installed first.
Arguments needed for recipes:
- macOS: name of the macOS you wish to download (macOS Ventura, 13.x, 22E for formats)
- format: package, application, image, iso 
- type: installer, firmware
- compat_only: Set to any value to only download compatible versions

Because of how [mist](https://github.com/ninxsoft/mist-cli) runs, the autopkg user needs passwordless sudo access for at least the mist cli tool, i.e.:

`autopkg_user ALL=(root) NOPASSWD: /usr/local/bin/mist`

## JamfPatchTitleVersioner.py
Autopkg processor that pulls the latest version for a given patch title. Arguments taken by this processoir:
- JSS_URL (Required): the URL of your Jamf server
- patch_softwaretitle (Required): The title of your patch title in Jamf
- CLIENT_ID: A Jamf API client_id
- CLIENT_SECRET: An associated Jamf API client_secret
- API_USERNAME: A User account with appropriate patch permissions in Jamf
- API_PASSWORD: The password for the above account

Either a combo of  **API_USERNAME and API_PASSWORD** or **CLIENT_ID and CLIENT_SECRET** are required, but CLIENT_ID and CLIENT_SECRET are take precedence.


## SleepIf.py
Shamefully ~~stolen from~~ inspired by [StopProcessingIf](https://github.com/autopkg/autopkg/blob/master/Code/autopkglib/StopProcessingIf.py) and [Sleep](https://github.com/autopkg/grahampugh-recipes/blob/main/CommonProcessors/Sleep.py) and modified, SleepIf takes the following arguments:
- predicate: NSPredicate-style comparison against an environment key
- sleep_time: The time, in seconds, to sleep
