import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter
import cv2
import numpy as np
from torch.autograd import Variable
import torch.nn as nn
import torch.utils.data as Data 
import torchvision
from PIL import Image,ImageOps
import os
from torch.utils.data import DataLoader
from collections import Counter



#this is the darknet architecutre from original paper,  we may use resnet50 in future 
#based on the training performance, but for now, we will observe the original paper
class Block(nn.Module):
    def __init__(self, in_channels, out_channels, **kwargs):
        super(Block, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, bias=False, **kwargs)
        self.batchnorm = nn.BatchNorm2d(out_channels)
        self.leakyrelu = nn.LeakyReLU(0.1)

    def forward(self, x):
        return self.leakyrelu(self.batchnorm(self.conv(x)))


class CROPPING_MODEL(nn.Module):
    def __init__(self, in_channels=3, **kwargs):
        super(CROPPING_MODEL, self).__init__()
        self.architecture = [(7, 64, 2, 3),"Max_Pooling",(3, 192, 1, 1),"Max_Pooling",(1, 128, 1, 0),(3, 256, 1, 1),(1, 256, 1, 0),(3, 512, 1, 1),
                "Max_Pooling",[(1, 256, 1, 0), (3, 512, 1, 1), 4],(1, 512, 1, 0),(3, 1024, 1, 1),"Max_Pooling",[(1, 512, 1, 0), (3, 1024, 1, 1), 2],
                (3, 1024, 1, 1),(3, 1024, 2, 1),(3, 1024, 1, 1),(3, 1024, 1, 1),]
        self.in_channels = in_channels
        self.darknet = self.original_darknet(self.architecture)
        self.fcs = self.build_fcs(**kwargs)

    def forward(self, x):
        x = self.darknet(x)
        return self.fcs(torch.flatten(x, start_dim=1))

    def original_darknet(self, architecture):
        layers = []
        in_channels = self.in_channels

        for x in architecture:
            if type(x) == tuple:
                layers += [Block(in_channels, x[1], kernel_size=x[0], stride=x[2], padding=x[3])]
                in_channels = x[1]

            elif type(x) == str:
                layers += [nn.MaxPool2d(kernel_size=(2, 2), stride=(2, 2))]

            elif type(x) == list:
                conv1 = x[0]
                conv2 = x[1]
                repeat_layers = x[2]

                for _ in range(repeat_layers):
                    layers += [Block(in_channels,conv1[1],kernel_size=conv1[0],stride=conv1[2],padding=conv1[3])]
                    layers += [Block(conv1[1],conv2[1],kernel_size=conv2[0],stride=conv2[2],padding=conv2[3])]
                    in_channels = conv2[1]

        return nn.Sequential(*layers)

    def build_fcs(self, grid_number, bounding_box_number, number_classes):
        S, B, C = grid_number, bounding_box_number, number_classes

        
        return nn.Sequential(nn.Flatten(),
                             nn.Linear(1024 * S * S, 4096),
                             nn.Dropout(0.25),
                             nn.LeakyReLU(0.1),
                             nn.Linear(4096, S * S * (C + B * 5)))




#load the trained CNN model to generate the prediction boxes
#cropping_process_model = CROPPING_MODEL(grid_number=7, bounding_box_number=2, number_classes=2).to("cpu")
#cropping_process_model = CROPPING_MODEL(grid_number=7, bounding_box_number=2, number_classes=2)

#cropping_process_model.load_state_dict(torch.load("model_cropping.pt",map_location=torch.device('cpu')))
#cropping_process_model.eval()

cropping_process_model=None
    # the function will take one single image with size (h,w,c), and predict the bounding box with also (h',w',c) shape image
def cropping_process(rotated_image, buffer):
    
    
    global cropping_process_model
    if cropping_process_model is None:
        cropping_process_model = CROPPING_MODEL(grid_number=7, bounding_box_number=2, number_classes=2).to("cpu")
        cropping_process_model.load_state_dict(torch.load("model_cropping_new333.pt",map_location=torch.device('cpu')))
        cropping_process_model.eval()
    
    
    
    #load the trained CNN model to generate the prediction boxes
   # cropping_process_model = CROPPING_MODEL(grid_number=7, bounding_box_number=2, number_classes=2).to("cpu")

    #cropping_process_model.load_state_dict(torch.load("model_cropping_new333.pt",map_location=torch.device('cpu')))
    #cropping_process_model.eval()
    
    
    
    
    
    # we may instead load the whole entire trained model
    #cropping_process_model = torch.load("tttmp.pt",map_location=torch.device('cpu'))
    #cropping_process_model.eval()
    
    
    
    # we observed the original paper that split the image into 7*7 grids, each grid will predict two boxes and choose the
    # better one, in our case, only two classes will be predicted;
    S=7
    B=2
    C=2
    #assign the input rotated image to image
    image = rotated_image
    #the way PIL read image has rotatded the original image 90 degree, so the function exif_transpose() will transpose it back
    #it could be different if you read image by cv2 library;
    image = ImageOps.exif_transpose(image)
    output_image = image
    #resize the image to 448*448*3 to fit the CNN model
    image = image.resize((448,448))
    #initial the image as np array
    data = np.array(image)
    #switch the dimension of the image from 448*448*3 to 3*448*448 to fit the model
    data = np.rollaxis(data, 2, 0)
   
    #convert the np array to torch tensor
    data = torch.tensor(data)
    data = data.float()
    data = data/255
    # add one demension to the data from 3*448*448 to 1*3*448*448
    data=data.unsqueeze(0)
    #print("the shape of image now is ")
    #print(data.shape)
    
    #plug the data to trained model to generate the predictions which will has a shape of 
    predictions = cropping_process_model(data)
    
    #predictions = predictions.to("cpu")
    
    #reshape the prediction to the shape of 1*7*7*12
    predictions = predictions.reshape(1, S, S, C+B*5)
    
    #print(predictions.shape)
    
    
    # getting the predicted value of the first bounding box
    front_bounding_box = predictions[:,:,:, 3:7]
    #print(front_bounding_box.shape)
    
    # getting the predicted value of the second bounding box
    back_bounding_box = predictions[:,:,:, 8:12]
    #print(back_bounding_box.shape)
    

    #compare the confidence score of two bounding boxes that contain an object, and pick the better one
    has_object_scores = torch.cat((predictions[:,:,:, 2].unsqueeze(0), predictions[:,:,:, 7].unsqueeze(0)), dim=0)
    #print(has_object_scores.shape)  (2*7*7*1)
    
    best_box = has_object_scores.argmax(0).unsqueeze(-1)
    #print(best_box)   (1*7*7*1)

    
    best_boxes = front_bounding_box * (1 - best_box) + best_box * back_bounding_box
    #print(best_boxes.shape) (1*7*7*4)
    
    
    order_cells = torch.arange(7).repeat(1, 7, 1).unsqueeze(-1)
    #print(order_cells)
    
    x = 1 / S * (best_boxes[:,:,:, :1] + order_cells)
    y = 1 / S * (best_boxes[:,:,:, 1:2] + order_cells.permute(0, 2, 1, 3))
    w_y = 1 / S * best_boxes[:,:,:, 2:4]
    
    #convert the prediction value and concat the bounding box 
    iteration_of_bounding_boxes = torch.cat((x, y, w_y), dim=-1)
    #print(iteration_of_bounding_boxes.shape)
    predicted_class = predictions[:,:,:, :2].argmax(-1).unsqueeze(-1)
    
    #keep the best score for containing an object
    best_confidence = torch.max(predictions[:,:,:, 2], predictions[:,:,:, 7]).unsqueeze(-1)
    #combine the class score, object score, and the better coordinates
    combined_new_predictions = torch.cat(
        (predicted_class, best_confidence, iteration_of_bounding_boxes), dim=-1
    )
    
    #reshape the matrix for iteration purpose
    converted_pred = combined_new_predictions.reshape(1, S * S, -1)
    converted_pred[:,:, 0] = converted_pred[:,:, 0].long()
    
    #print(converted_pred.shape)
        
    bboxes = []

    for i in range(S * S):
        bboxes.append([x.item() for x in converted_pred[0, i, :]])
    
    
    #we will assume the possibility has to be larger than 0.5 to have an object
    threshold = 0.5
    new_bboxes = []
    for box in bboxes:
        if box[1] >= threshold:
            new_bboxes.append(box)
        
   
    #print(bboxes)
    # if all the prediction posibility of containing an object is less than 0.5, we will give a minimum prediction 0.3 and 
    #find the maximum posibility box from all the boxes; 
    # if there are more than two boxes that is larger posibility than threshold, we will filter out the smaller ones for each type
    # to make sure each type of headstones will be showed only once
    max_box = 0.0
    max_regular_headstone = 0.0
    max_outliner_headstone = 0.0
    tmp_max_regular_headstone = []
    tmp_max_outliner_headstone = []
    new_new_bboxes = []
    if len(new_bboxes) == 0:
        
        for box in bboxes:
            if box[1] > max_box and box[1]>0.3:
            #if box[1] > max_box:

                #print(box[1])
                max_box = box[1]
                tmp_max_box = box
        new_bboxes.append(tmp_max_box)
        new_new_bboxes = new_bboxes
    elif len(new_bboxes)>=2:
        
        for box in new_bboxes:
            if box[0] == 0.0:
                if box[1] > max_regular_headstone:
                    max_regular_headstone = box[1]
                    tmp_max_regular_headstone = box
            else:
                if box[1] > max_outliner_headstone:
                    max_outliner_headstone = box[1]
                    tmp_max_outliner_headstone = box
                    
    if tmp_max_regular_headstone:
        new_new_bboxes.append(tmp_max_regular_headstone)
    if tmp_max_outliner_headstone:
        new_new_bboxes.append(tmp_max_outliner_headstone)

    
    if len(new_bboxes)==1:
        new_new_bboxes = new_bboxes
        
    bboxes = new_new_bboxes
    
    
    
    data=data.squeeze(0)
    data = data.permute(1,2,0)*255
    #plt.imshow(data)
    #print(data.int())
    data = data.int()
    im = np.array(output_image)
    #print(im.shape)
    height = im.shape[0]
    width = im.shape[1]
   
    #fig, ax = plt.subplots(1)
    # show the original image
    #ax.imshow(im)
    cropped_headstones = []
    #assume we might have multiple objects (really rare)
    for box in bboxes:
        box = box[2:]
        upper_left_x = box[0] - box[2] / 2
        upper_left_y = box[1] - box[3] / 2   
        
        
        #rect = patches.Rectangle((upper_left_x * width, upper_left_y * height),box[2] * width,box[3] * height,linewidth=1.5,edgecolor="black",facecolor="none")
        
        # we add a max function here because the predicted box maybe out of the bounary of the original image
        # we add a max function here because the predicted box maybe out of the bounary of the original image
        x_left_absolute = max(int(upper_left_y * height)-buffer,0)
        #print(x_left_absolute)
        x_right_absolute = min(int(upper_left_y*height+box[3]*height)+buffer,height-1)
        #print(x_right_absolute)

        y_left_absolute = max(int(upper_left_x * width)-buffer,0)
        #print(y_left_absolute)

        y_right_absolute = min(int(upper_left_x * width+box[2] * width)+buffer,width-1)
        #print(y_right_absolute)
        
        headstone=im[x_left_absolute:x_right_absolute,y_left_absolute:y_right_absolute,:]
        #tmp=Image.fromarray(headstone)
        #plt.imshow(tmp)
        cropped_headstones.append(headstone)
        
        
        
        
        #print(rect)
        #print(bboxes)
        #ax.add_patch(rect)
        
        #print(headstone.shape)
        
    #plt.show()
    
    # the function will return a list that contains the cropped headstone, but for testing purpose, we will just let it showed
    #return cropped_headstones
    
    #print(len(cropped_headstones))
    #for headstone in cropped_headstones:
        
        
        #cropped=Image.fromarray(headstone)
        
        
        #we can store the cropped headstone to the folder by 
        #cropped.save('cropped_image.jpg')
        
        #for testing, we just want to show the result
        #plt.imshow(cropped)
        
        # the variable OCR_input_cropped_headstone will be sent to OCR() function
        #OCR_input_cropped_headstone = np.array(headstone)
    
    
    return cropped_headstones[0]

    

if __name__ == "__main__":
    # here are the images we read from file, we will send the images one by one, read the image by PIL library
    image = Image.open("testing_image.jpg")

    
        
    #call the function, cropped variable will be np array
    cropped = cropping_process(image,100)

    #convert np array to image
    #cropped=Image.fromarray(cropped)

    #show the cropped image
    #plt.imshow(cropped)    
    




