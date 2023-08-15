import cv2
import depthai as dai
class OAKD:
    def __init__(self, width, height):
        # Start defining a pipeline
        self.pipeline = dai.Pipeline()
        cam_rgb = self.pipeline.createColorCamera()
        cam_rgb.setPreviewSize(width, height)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
        cam_rgb.setFps(40)

        cam_rgb_xout = self.pipeline.createXLinkOut()
        cam_rgb_xout.setStreamName("rgb")
        cam_rgb.preview.link(cam_rgb_xout.input)

        # Pipeline defined, now the device is connected to
        self.device = dai.Device(self.pipeline)
    def read(self):
        q_rgb = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False).get()
        frame_rgb = q_rgb.getCvFrame()
        return frame_rgb