# 查看文件夹下有多少文件
import os
import subprocess
import time


def count_files_in_folder(folder_path):
	file_count = 0
	for _, _, files in os.walk(folder_path):
		file_count += len(files)
	return file_count


# 写入批处理文件
def append_to_file(file_path, content):
	with open(file_path, 'a') as file:
		file.write(content)


# facefunction
def facefunction(img_file, ffmpeg_magic, ffmpeg_facefunction):
	# 拆分视频
	file_count = count_files_in_folder(ffmpeg_magic)

	txt_file_path = '/Users/zyooo/Desktop/project/facefusion/batch.txt'

	# 遍历每个输出的图片去批处理换脸
	for i in range(file_count):
		content_to_add = '-t /Users/zyooo/Desktop/project/facefusion/test/face_{:04d}.jpg\n'.format(i)
		append_to_file(txt_file_path, content_to_add)

	command = [
		"python " +
		"/opt/facefunction/run-batch.py " +
		" --batch batch.txt " +
		" --frame-processors face_swapper face_enhancer " +
		" --execution-providers cuda " +
		" --skip-download " +
		" --headless "
	]


def testffmpegmagic():
	command = [
		"ffmpeg " +
		"-i " +
		" /Users/zyooo/Desktop/test/test.mp4 " +
		" -vf " + " fps=15 " +
		" /Users/zyooo/Desktop/test/magic/magic_%04d.jpg"
	]
	subprocess.run(command, shell=True)
	print("视频拆分完成  ", "time:", time.time())


def testffmpegface():
	command = [
		"ffmpeg " +
		" -r  15" +
		" -i  /Users/zyooo/Desktop/test/face/face_%04d.jpg " +
		" -vcodec libx264 " +
		" -pix_fmt yuv420p " +
		" /Users/zyooo/Desktop/test/facefunction.mp4"
	]
	subprocess.run(command, shell=True)
	print("视频合成完成  ", "time:", time.time())


if __name__ == "__main__":
	# testffmpegmagic()
	# facefunction("/Users/zyooo/Desktop/test/face1.jpg", "/Users/zyooo/Desktop/test/magic",
	# 		 "/Users/zyooo/Desktop/test/face")
	testffmpegface()
