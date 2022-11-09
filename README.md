# UpdateTitleEditor
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
