import os
import shutil
import subprocess
import threading
import time

import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from gradio_client import Client

app = FastAPI()
lock = threading.Lock()


# 查看文件夹下有多少文件
def count_files_in_folder(folder_path):
	file_count = 0
	for _, _, files in os.walk(folder_path):
		file_count += len(files)
	return file_count


# magic
def generate_animation(reference_image_url, motion_sequence_url, seed, steps, guidance_scale):
	client = Client("http://172.19.19.5:7860/")
	result = client.predict(
		reference_image_url,
		motion_sequence_url,
		seed,
		steps,
		guidance_scale,
		fn_index=2
	)
	return result


# 写入批处理文件
def append_to_file(file_path, content):
	with open(file_path, 'a') as file:
		file.write(content)


# facefunction
def facefunction(img_file, ffmpeg_magic, ffmpeg_facefunction):
	# 拆分视频
	file_count = count_files_in_folder(ffmpeg_magic)
	# 批处理文件路径
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
	try:
		subprocess.run(command, shell=True, check=True)
	except subprocess.CalledProcessError:
		return


def facefunction_frame(source_img, target_file, output_file):
	# 换脸+脸部增强+超分
	command = [
		"python " +
		"/opt/facefusion/run.py " +
		" --source " +
		source_img +
		" --target " +
		target_file +
		" --output " +
		output_file +
		" --frame-processors face_swapper face_enhancer frame_enhancer " +
		" --face-enhancer-model gfpgan_1.4 " +
		" --frame-enhancer-model real_esrgan_x2plus " +
		" --execution-providers cuda tensorrt " +
		" --output-image-quality 90 " +
		" --face-enhancer-blend 90 " +
		" --frame-enhancer-blend 90 " +
		" --keep-fps " +
		" --skip-download " +
		" --headless "
	]
	try:
		subprocess.run(command, shell=True, check=True)
	except subprocess.CalledProcessError:
		return


def add_watermark_and_music(video_url, watermark_url, music_url, output_path):
	watermark_file = "/var/shared/watermark.png"
	music_file = "/var/shared/music.mp3"

	# 执行 curl 命令下载文件
	subprocess.run(["curl", "-o", watermark_file, watermark_url])
	subprocess.run(["curl", "-o", music_file, music_url])

	cmd = f"ffmpeg -i {video_url} -i {watermark_file}  -i {music_file} -filter_complex '[0:v][1:v]overlay=W-w-24:H-h-24[v];[v][2:a]concat=n=1:v=1:a=1[out]' -map '[out]' -c:v libx264 -c:a aac -shortest -y {output_path}"

	try:
		subprocess.run(cmd, shell=True, check=True)
	except subprocess.CalledProcessError:
		return

	while not os.path.exists(output_path):
		time.sleep(1)

	return output_path


@app.get("/generate_animation")
def generate_animation_endpoint(request: Request):
	lock.acquire()
	try:
		# uid = request.query_params.get("uid")
		image = request.query_params.get("image")
		motion_video = request.query_params.get("motion_video")
		seed = request.query_params.get("seed")
		steps = request.query_params.get("steps")
		guidance_scale = request.query_params.get("guidance_scale")
		music = request.query_params.get("music")
		watermark = request.query_params.get("water_mark")

		# magic
		files = [
			"/var/shared/source.jpg",
			"/var/shared/success.mp4",
			"/var/shared/magic.mp4",
			"/var/shared/music.mp3",
			"/var/shared/watermark.png",
			"/var/shared/facefusion_frame.mp4",
			"/var/shared/facefusion_success.mp4"
		]
		folder = [
			"/var/shared/ffmpeg_magic",
			"/var/shared/ffmpeg_facefunction"
		]
		for folder_path in folder:
			if os.path.exists(folder_path):
				shutil.rmtree(folder_path)
		for file_path in files:
			if os.path.exists(file_path):
				os.remove(file_path)
		print("清理完成")

		result = generate_animation(
			image,
			motion_video,
			seed,
			steps,
			guidance_scale,
		)
		print("magic完成：", result, " time:", time.time())

		os.makedirs("/var/shared/ffmpeg_magic", exist_ok=True)
		command = [
			"ffmpeg " +
			"-i " +
			" /var/shared/magic.mp4 " +
			" -vf " + " fps=15 " +
			"/var/shared/ffmpeg_magic/magic_%04d.jpg"
		]
		try:
			subprocess.run(command, shell=True, check=True)
			print("视频拆分完成  ", "time:", time.time())
		except subprocess.CalledProcessError:
			return

		# facefunction
		facefunction_frame_path = " /var/shared/facefusion_frame.mp4"
		facefunction_success = " /var/shared/facefusion_success.mp4"

		img = requests.get(image).content
		with open(os.path.join("/var/shared", "source.jpg"), "wb") as f:
			f.write(img)
		img_file = "/var/shared/source.jpg"

		os.makedirs("/var/shared/ffmpeg_facefunction", exist_ok=True)

		facefunction(img_file, "/var/shared/ffmpeg_magic", "/var/shared/ffmpeg_facefunction")
		print("facefunction换脸完成  ", "time:", time.time())

		command = [
			"ffmpeg " +
			" -r  15" +
			" -i  /var/shared/ffmpeg_facefunction/face_%04d.jpg " +
			" -vcodec libx264 " +
			" -pix_fmt yuv420p " +
			facefunction_frame_path
		]
		try:
			subprocess.run(command, shell=True, check=True)
			print("视频合成完成  ", "time:", time.time())
			facefunction_frame(img_file, facefunction_frame_path, facefunction_success)
			print("facefunction超分完成  ", "time:", time.time())
			if os.path.exists(facefunction_success):
				output_path = add_watermark_and_music(facefunction_success, watermark, music, "/var/shared/success.mp4")
				print("ffmpeg完成 time", time.time())
				return StreamingResponse(open(output_path, "rb"), media_type="video/mp4")
			else:
				return {"status": 500, "message": "合成音频和水印失败"}
		except subprocess.CalledProcessError:
			return
	finally:
		lock.release()


if __name__ == "__main__":
	import uvicorn

	uvicorn.run(app, host="0.0.0.0", port=8000)
