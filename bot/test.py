files = ['2021-07-25_04-11-49_UTC_1.jpg', '2021-07-25_04-11-49_UTC_1.mp4']
for file in files:
	if 'mp4' in file:
		files.remove(file[:-4] + '.jpg')
		
print(files)