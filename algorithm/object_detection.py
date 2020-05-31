import os.path
import time
import uuid
from pathlib import Path

import cv2
import imageio
import numpy as np

CUR_DIR = (Path(__file__).parent).absolute()
STATIC_DIR = CUR_DIR.parent / "static"
IMAGE_DIR = STATIC_DIR / "img"

# Initialize the parameters
confThreshold = 0.5  # Confidence threshold
nmsThreshold = 0.4  # Non-maximum suppression threshold
inpWidth = 416  # Width of network's input image
inpHeight = 416  # Height of network's input image

# Load names of classes
dir_name = "/yolo/"
classFile = os.path.join(dir_name, "coco.names")
classes = None
with open(classFile, "rt") as f:
    classes = f.read().rstrip("\n").split("\n")

# Give the configuration and weight files for the model and load the network using them
modelConfiguration = os.path.join(dir_name, "yolov3.cfg")
modelWeights = os.path.join(dir_name, "yolov3.weights")

net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)


# Get the names of the output layers
def getOutputNames(net: str):
    # Get the names of all the layers in the network
    layersNames = net.getLayerNames()
    # Get the names of the output layers
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]


# Draw the predicted bounding box
def drawPred(frame, classId, conf, left, top, right, bottom):
    # Draw a bounding box
    cv2.rectangle(frame, (left, top), (right, bottom), (255, 178, 50), 3)

    label = "%.2f" % conf

    # Get the label for the class name and its confidence
    if classes:
        assert classId < len(classes)
        label = "%s:%s" % (classes[classId], label)

    # Display the label at the top of the bounding box
    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv2.rectangle(
        frame,
        (left, top - round(1.5 * labelSize[1])),
        (left + round(1.5 * labelSize[0]), top + baseLine),
        (255, 255, 255),
        cv2.FILLED,
    )
    cv2.putText(frame, label, (left, top), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 1)


# Remove the bounding boxes with low confidence using non-maxima supression
def postprocess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores.
    # Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant
    # overlapping boxes with lower confidences
    indices = cv2.dnn.NMSBoxes(boxes, confidences, confThreshold, nmsThreshold)
    results = dict()
    results["image_size"] = {"width": frameWidth, "height": frameHeight}
    results["objects"] = []
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(
            frame, classIds[i], confidences[i], left, top, left + width, top + height
        )
        results["objects"].append(
            {
                "name": classes[classIds[i]],
                "left": left,
                "top": top,
                "right": left + width,
                "bottom": top + height,
            }
        )
    return results


def obj_detection(in_path, input_type="video"):
    cap = cv2.VideoCapture(in_path)

    # video capture 1fps limits 3 seconds
    frame_count = 0
    frame_rate = 5
    frame_time = 3
    prev = 0

    file_name = str(uuid.uuid4()) + ".gif"
    output_file = os.path.join(IMAGE_DIR, file_name)
    # output_file = file_name
    # frame_width = int(cap.get(3))
    # frame_height = int(cap.get(4))
    # out = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'MPV4'),
    #     frame_rate, (frame_width, frame_height))

    images = []
    total_time = 0
    results = dict()
    while True:
        if frame_count > frame_rate * frame_time:
            print(f"limit over {frame_time} seconds, cutting...")
            break

        time_elapsed = time.time() - prev
        ret, frame_temp = cap.read()

        if frame_temp is None:
            print("frame is None")
            break
        frame = frame_temp

        if time_elapsed > 1.0 / frame_rate:
            prev = time.time()

            # Create a 4D blob from a frame
            blob = cv2.dnn.blobFromImage(
                frame, 1 / 255, (inpWidth, inpHeight), [0, 0, 0], 1, crop=False
            )

            # Sets the input to the network
            net.setInput(blob)

            # Runs the forward pass to get output of the output layers
            outs = net.forward(getOutputNames(net))

            # Remove the bounding boxes with low confidence
            results = postprocess(frame, outs)

            # Put efficiency information.
            # The function getPerfProfile returns the overall time
            # for inference(t) and the timing for each of the layers(in layerTimes)
            t, _ = net.getPerfProfile()
            process_time = t * 1000.0 / cv2.getTickFrequency()
            label = "Inference time: %.2f ms" % process_time
            cv2.putText(
                frame, label, (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255)
            )

            total_time += process_time

            # out.write(frame)
            frame_count += 1
            if input_type == "image":
                break
            images.append(frame)

    results["time"] = total_time

    # Write the frame with the detection boxes
    print(f"frame_count : {frame_count}")
    if frame_count == 0:
        return {}
    elif frame_count == 1:
        file_name = file_name[:-4] + ".jpg"
        output_file = output_file[:-4] + ".jpg"
        cv2.imwrite(output_file, frame.astype(np.uint8))
    else:
        imageio.mimsave(output_file, images)

    # TODO: change url path
    results["url_path"] = os.path.join("/static", "img", file_name)
    results["file_path"] = output_file
    cap.release()

    return results
