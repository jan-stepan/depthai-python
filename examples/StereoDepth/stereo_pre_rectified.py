#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np
from pathlib import Path
import argparse

class StereoConfigHandler:

    class Trackbar:
        def __init__(self, trackbarName, windowName, minValue, maxValue, defaultValue, handler):
            self.min = minValue
            self.max = maxValue
            self.windowName = windowName
            self.trackbarName = trackbarName
            cv2.createTrackbar(trackbarName, windowName, minValue, maxValue, handler)
            cv2.setTrackbarPos(trackbarName, windowName, defaultValue)

        def set(self, value):
            if value < self.min:
                value = self.min
                print(f'{self.trackbarName} min value is {self.min}')
            if value > self.max:
                value = self.max
                print(f'{self.trackbarName} max value is {self.max}')
            cv2.setTrackbarPos(self.trackbarName, self.windowName, value)

    newConfig = False
    config = None
    trConfidence = list()
    trLrCheck = list()
    trCostAggregationP1 = list()
    trCostAggregationP2 = list()
    trOutlierRemovalThreshold = list()
    trOutlierCensusThreshold = list()
    trOutlierDiffThreshold = list()

    def trackbarConfidence(value):
        StereoConfigHandler.config.costMatching.confidenceThreshold = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trConfidence:
            tr.set(value)

    def trackbarLrCheckThreshold(value):
        StereoConfigHandler.config.algorithmControl.leftRightCheckThreshold = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trLrCheck:
            tr.set(value)

    def trackbarCostAggregationP1(value):
        StereoConfigHandler.config.costAggregation.horizontalPenaltyCostP1 = value
        StereoConfigHandler.config.costAggregation.verticalPenaltyCostP1 = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trCostAggregationP1:
            tr.set(value)

    def trackbarCostAggregationP2(value):
        StereoConfigHandler.config.costAggregation.horizontalPenaltyCostP2 = value
        StereoConfigHandler.config.costAggregation.verticalPenaltyCostP2 = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trCostAggregationP2:
            tr.set(value)

    def trackbarOutlierRemovalThreshold(value):
        StereoConfigHandler.config.algorithmControl.outlierRemoveThreshold = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trOutlierRemovalThreshold:
            tr.set(value)

    def trackbarOutlierCensusThreshold(value):
        StereoConfigHandler.config.algorithmControl.outlierCensusThreshold = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trOutlierCensusThreshold:
            tr.set(value)

    def trackbarOutlierDiffThreshold(value):
        StereoConfigHandler.config.algorithmControl.outlierDiffThreshold = value
        StereoConfigHandler.newConfig = True
        for tr in StereoConfigHandler.trOutlierDiffThreshold:
            tr.set(value)


    def handleKeypress(key, stereoDepthConfigInQueue):
        if key == ord('l'):
            StereoConfigHandler.newConfig = True
            currentCfg = StereoConfigHandler.config.costAggregation.localAggregationMode
            nextCfg = cfgSettings[(cfgSettings.index(currentCfg)+1) % len(cfgSettings)]
            print(f"Changing local aggregation to {nextCfg.name} from {currentCfg.name}")
            StereoConfigHandler.config.costAggregation.localAggregationMode = nextCfg
        elif key == ord('r'):
            StereoConfigHandler.newConfig = True
            currentCfg = StereoConfigHandler.config.algorithmControl.replaceInvalidDisparity
            nextCfg = not currentCfg
            print(f"Changing replace invalid disparity to {nextCfg} from {currentCfg}")
            StereoConfigHandler.config.algorithmControl.replaceInvalidDisparity = nextCfg

        StereoConfigHandler.sendConfig(stereoDepthConfigInQueue)

    def sendConfig(stereoDepthConfigInQueue):
        if StereoConfigHandler.newConfig:
            StereoConfigHandler.newConfig = False
            configMessage = dai.StereoDepthConfig()
            configMessage.set(StereoConfigHandler.config)
            configMessage.setData([1]) # NOTE workaround
            stereoDepthConfigInQueue.send(configMessage)

    def updateDefaultConfig(config):
        StereoConfigHandler.config = config

    def registerWindow(stream):
        cv2.namedWindow(stream, cv2.WINDOW_NORMAL)

        StereoConfigHandler.trConfidence.append(StereoConfigHandler.Trackbar('Disparity confidence', stream, 0, 255, StereoConfigHandler.config.costMatching.confidenceThreshold, StereoConfigHandler.trackbarConfidence))
        StereoConfigHandler.trCostAggregationP1.append(StereoConfigHandler.Trackbar('Cost aggregation P1', stream, 0, 500, StereoConfigHandler.config.costAggregation.horizontalPenaltyCostP1, StereoConfigHandler.trackbarCostAggregationP1))
        StereoConfigHandler.trCostAggregationP2.append(StereoConfigHandler.Trackbar('Cost aggregation P2', stream, 0, 500, StereoConfigHandler.config.costAggregation.horizontalPenaltyCostP2, StereoConfigHandler.trackbarCostAggregationP2))
        StereoConfigHandler.trLrCheck.append(StereoConfigHandler.Trackbar('Left-right check threshold', stream, 0, 255, StereoConfigHandler.config.algorithmControl.leftRightCheckThreshold, StereoConfigHandler.trackbarLrCheckThreshold))
        StereoConfigHandler.trOutlierRemovalThreshold.append(StereoConfigHandler.Trackbar('Outlier removal threshold', stream, 0, 49, StereoConfigHandler.config.algorithmControl.outlierRemoveThreshold, StereoConfigHandler.trackbarOutlierRemovalThreshold))
        StereoConfigHandler.trOutlierCensusThreshold.append(StereoConfigHandler.Trackbar('Outlier census threshold', stream, 32, 255, StereoConfigHandler.config.algorithmControl.outlierCensusThreshold, StereoConfigHandler.trackbarOutlierCensusThreshold))
        StereoConfigHandler.trOutlierDiffThreshold.append(StereoConfigHandler.Trackbar('Outlier difference threshold', stream, 1, 96, StereoConfigHandler.config.algorithmControl.outlierDiffThreshold, StereoConfigHandler.trackbarOutlierDiffThreshold))

    def __init__(self, config):

        StereoConfigHandler.config = config



datasetDefault = str((Path(__file__).parent / Path('../models/dataset')).resolve().absolute())
if not Path(datasetDefault).exists():
    import sys
    raise FileNotFoundError(f'Required file/s not found, please run "{sys.executable} install_requirements.py"')

left = datasetDefault + '/' + '0' + '/' + 'in_left' + '.png'
right = datasetDefault + '/' + '0' + '/' + 'in_right' + '.png'


inW = 1920
inH = 1200
# inW = 1280
# inH = 800

# left = "horizontal-rectified_left_screenshot_13.04.2023.png"
# right = "horizontal-rectified_right_screenshot_13.04.2023.png"

leftImg = cv2.imread(left, cv2.IMREAD_GRAYSCALE)
rightImg = cv2.imread(right, cv2.IMREAD_GRAYSCALE)
leftImg = cv2.resize(leftImg, (inW,inH))
rightImg = cv2.resize(rightImg, (inW,inH))

width = leftImg.shape[1]
height = leftImg.shape[0]

cv2.imshow("leftImg", leftImg)
cv2.imshow("rightImg", rightImg)
cv2.waitKey(1) 

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs

monoLeft = pipeline.create(dai.node.XLinkIn)
monoRight = pipeline.create(dai.node.XLinkIn)
xoutLeft = pipeline.create(dai.node.XLinkOut)
xoutRight = pipeline.create(dai.node.XLinkOut)
xoutDepth = pipeline.create(dai.node.XLinkOut)
stereo = pipeline.create(dai.node.StereoDepth)

monoLeft.setStreamName("inLeft")
monoRight.setStreamName("inRight")
xoutLeft.setStreamName("left")
xoutRight.setStreamName("right")
xoutDepth.setStreamName("depth")


monoLeft.setMaxDataSize(width * height)
monoRight.setMaxDataSize(width * height)

# Linking
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)
stereo.syncedLeft.link(xoutLeft.input)
stereo.rectifiedRight.link(xoutRight.input)
stereo.disparity.link(xoutDepth.input)
stereo.setInputResolution(width,height) # set input resolution specifically

stereo.setRectification(True) #disable rectification, frames are pre-rectified

stereo.setLeftRightCheck(False)
stereo.setSubpixel(True)
stereo.setSubpixelFractionalBits(5)


stereo.setConfidenceThreshold(230)

# config = stereo.initialConfig.get()
# config.algorithmControl.enableLeftRightCheck = False
# config.algorithmControl.leftRightCheckThreshold = 10
# config.algorithmControl.replaceInvalidDisparity = False
# config.algorithmControl.outlierRemoveThreshold = 49
# config.algorithmControl.outlierCensusThreshold = 255
# config.algorithmControl.outlierDiffThreshold = 96
# config.costMatching.confidenceThreshold = 230
# config.costAggregation.localAggregationMode = dai.StereoDepthConfig.CostAggregation.LocalAggregationMode.PASS3x3 #CLAMP3x3, PASS3x3
# stereo.initialConfig.set(config)


StereoConfigHandler(stereo.initialConfig.get())
StereoConfigHandler.registerWindow('Stereo control panel')

xinStereoDepthConfig = pipeline.create(dai.node.XLinkIn)
xinStereoDepthConfigName = "stereoDepthConfig"
xinStereoDepthConfig.setStreamName(xinStereoDepthConfigName)
xinStereoDepthConfig.out.link(stereo.inputConfig)


# Connect to device and start pipeline
with dai.Device(pipeline) as device:

    qInLeft = device.getInputQueue("inLeft")
    qInRight = device.getInputQueue("inRight")
    qLeft = device.getOutputQueue("left", 4, False)
    qRight = device.getOutputQueue("right", 4, False)
    qDepth = device.getOutputQueue("depth", 4, False)

    cnt = 0

    while True:

        data = cv2.resize(leftImg, (width, height), interpolation = cv2.INTER_AREA)

        data = data.reshape(height*width)
        img = dai.ImgFrame()
        img.setData(data)
        img.setInstanceNum(1)
        img.setType(dai.ImgFrame.Type.RAW8)
        img.setWidth(width)
        img.setHeight(height)
        # print("left send")
        qInLeft.send(img)

        data = cv2.resize(rightImg, (width, height), interpolation = cv2.INTER_AREA)
        data = data.reshape(height*width)
        img = dai.ImgFrame()
        img.setData(data)
        img.setInstanceNum(2)
        img.setType(dai.ImgFrame.Type.RAW8)
        img.setWidth(width)
        img.setHeight(height)
        qInRight.send(img)
        # print("right send")

        inLeft = qLeft.get()
        frameLeft = inLeft.getCvFrame()
        cv2.imshow("left", frameLeft)

        inRight = qRight.get()
        frameRight = inRight.getCvFrame()
        cv2.imshow("right", frameRight)

        inDepth = qDepth.get()

        data = np.array(inDepth.getData())

        count = np.count_nonzero(data % 32 == 0)
        # print("Non multiples of 32 in disparity: ", count, " out of ", len(data), " (", count/len(data)*100, "%)")

        frameDepth = inDepth.getCvFrame()
        # cv2.imshow("depth", frameDepth)

        disp = (frameDepth / 32).astype(np.uint8)
        cv2.imshow("disp", disp)

        cnt+=1


        key = cv2.waitKey(1)
        if key == ord('q'):
            break

        StereoConfigHandler.handleKeypress(key, device.getInputQueue(xinStereoDepthConfigName))
