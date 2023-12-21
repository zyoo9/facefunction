def append_to_file(file_path, content):
	with open(file_path, 'a') as file:
		file.write(content)


# 指定txt文件路径和要添加的内容
txt_file_path = '/Users/zyooo/Desktop/project/facefusion/test-batch.txt'
# 循环10次，生成并添加字符串到txt文件中
for i in range(1, 11):
    content_to_add = '-t /Users/zyooo/Desktop/project/facefusion/test/face_{:04d}.jpg\n'.format(i)
    append_to_file(txt_file_path, content_to_add)
