import PySpin
import pyglet
from pyglet.gl import *
import numpy as np

from simple_pyspin import Camera

# behavior camera====================================================================
# connect to a flir camera and take frames with times that are on the same clock as the task
# cam = Camera(index='20442803')#change to proper SN
# cam.init()
# cam.start()
# imgs = []

# camera_timestamps = []s
# frame_array = cam.get_array()
# print(np.shape(frame_array))


import PySpin
import cv2
import time
import imageio
import numpy as np

# Initialize the camera system
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)
cam.Init()

# Start capturing images
cam.BeginAcquisition()

# Setup parameters for high quality video output
output_filename = 'output_high_quality.mp4'
fps = 34.8  # Adjust based on your camera's capabilities
codec = 'libx265'  # H.264 codec; widely supported & good quality
bitrate = '5M'  # Higher bitrate for better quality, adjust as necessary

writer = imageio.get_writer(output_filename, fps=fps, codec=codec, bitrate=bitrate, macro_block_size=None)

# Initialize variables for FPS calculation
frame_count = 0
start_time = time.time()

try:
    while True:
        # Capture image
        image_result = cam.GetNextImage()
        if image_result.IsIncomplete():
            print(f"Image incomplete with image status {image_result.GetImageStatus()}...")
        else:
            # Get the image data as a NumPy array
            image_data = image_result.GetNDArray()

            # Resize the image
            frame_size = (320, 240)  # Match the size of the resized images
            resized_image = cv2.resize(image_data, frame_size)

            # Ensure image is in the correct format (convert to RGB if needed)
            if len(resized_image.shape) == 2 or resized_image.shape[2] == 1:  # If grayscale
                resized_image = cv2.cvtColor(resized_image, cv2.COLOR_GRAY2RGB)

            # Write frame to video file
            writer.append_data(resized_image)

            # Display the image using OpenCV
            cv2.imshow('FLIR Camera Stream', resized_image)

            # FPS calculation and display
            frame_count += 1
            if frame_count >= 30:  # Update FPS in the console every 30 frames
                end_time = time.time()
                elapsed_time = end_time - start_time
                fps = frame_count / elapsed_time
                print(f"FPS: {fps:.2f}")
                frame_count = 0
                start_time = time.time()

            # Check for a key press to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release the image for the next frame
        image_result.Release()

except KeyboardInterrupt:
    pass

finally:
    # Cleanup
    cam.EndAcquisition()
    cam.DeInit()
    del cam
    cam_list.Clear()
    system.ReleaseInstance()
    writer.close()  # Make sure to close the writer
    cv2.destroyAllWindows()




