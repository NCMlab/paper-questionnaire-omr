On the development server: 
List the files in teh Dropbox folder
 rclone ls DropboxRClone:
 rclone lsd DropboxRClone:

# This command syncs all files from Fropbox to the local Developer server. It only copies new ones.
# I may be able to remove the interactive command.
 rclone sync --interactive /home/steffejr/PaperQuestionnaires/DropboxFolder DropboxRClone:incoming
