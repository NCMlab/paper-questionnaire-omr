On the development server: 
List the files in teh Dropbox folder
 rclone ls DropboxRClone:
 rclone lsd DropboxRClone:

# This command syncs all files from Fropbox to the local Developer server. It only copies new ones.
# I may be able to remove the interactive command.
 rclone sync --interactive /home/steffejr/PaperQuestionnaires/DropboxFolder DropboxRClone:incoming
rclone sync  DropboxRClone:incoming ~/PaperQuestionnaires/DropboxFolder/

I can use VSCode an connect to teh code onteh development server to edits .tex files and the PDF

To add the questionnaire ID:
https://sdaps.org/getting-started/more/
Also run 
sdaps.py stamp PROJECT/ -r 5


~/PaperQuestionnaires/sdaps/sdaps.py add --convert GAS003/ ~/PaperQu
estionnaires/DropboxFolder/Adobe\ Scan\ Jun.\ 08,\ 2026.pdf 

convert ~/PaperQuestionnaires/DropboxFolder/Adobe\ Scan\ Jun.\ 08,\ 2026.pdf -monochrome -compress Group4 TestGAS.tiff


## Start the broadway
Here are the commands from yesterday:

Start the Broadway display server (background):


broadwayd :5 &
Launch the sdaps GUI via Broadway:


GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 ~/PaperQuestionnaires/sdaps/sdaps.py gui ~/PaperQuestionnaires/paper-questionnaire-omr/sdaps_pipeline/projects/gas-en/

https://jatos-dev.ncmlab.ca/broadway/


On the development server: 
List the files in teh Dropbox folder
 rclone ls DropboxRClone:
 rclone lsd DropboxRClone:

# This command syncs all files from Fropbox to the local Developer server. It only copies new ones.
# I may be able to remove the interactive command.
 rclone sync --interactive /home/steffejr/PaperQuestionnaires/DropboxFolder DropboxRClone:incoming
rclone sync  DropboxRClone:incoming ~/PaperQuestionnaires/DropboxFolder/

I can use VSCode an connect to teh code onteh development server to edits .tex files and the PDF

To add the questionnaire ID:
https://sdaps.org/getting-started/more/
Also run 
sdaps.py stamp PROJECT/ -r 5


~/PaperQuestionnaires/sdaps/sdaps.py add --convert GAS003/ ~/PaperQu
estionnaires/DropboxFolder/Adobe\ Scan\ Jun.\ 08,\ 2026.pdf 

convert ~/PaperQuestionnaires/DropboxFolder/Adobe\ Scan\ Jun.\ 08,\ 2026.pdf -monochrome -compress Group4 TestGAS.tiff


## Start the broadway
Here are the commands from yesterday:

Start the Broadway display server (background):


broadwayd :5 &
Launch the sdaps GUI via Broadway:


GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 ~/PaperQuestionnaires/sdaps/sdaps.py gui ~/PaperQuestionnaires/paper-questionnaire-omr/sdaps_pipeline/projects/gas-en/

https://jatos-dev.ncmlab.ca/broadway/


sdaps.py export ocr-training -f "verified" JASONtest/GAS006