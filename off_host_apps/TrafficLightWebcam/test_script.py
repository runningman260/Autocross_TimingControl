import os

script_wd = os.path.abspath(os.path.dirname(__file__))
image_folder_name = "StartLineImages"
image_folder_path = script_wd + r"/" + image_folder_name
if(not os.path.isdir(image_folder_path)):
	print("Does not Exist")
	os.makedirs(image_folder_path)