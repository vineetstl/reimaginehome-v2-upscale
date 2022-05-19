import argparse
import cv2
import glob
import os

from realesrgan import RealESRGANer
# from flask import Flask
# from flask_cors import CORS
# from flask import request
# from flask import render_template
import torch
import random
import string
import datetime
from PIL import Image
import requests
import boto3
import json

# app = Flask(__name__)
# CORS(app)

# secret_file = open("./secrets.json")
# secrets = json.load(secret_file)

# s3 = boto3.resource('s3',
#     aws_access_key_id=secrets["accessID"],
#     aws_secret_access_key=secrets["accessKey"],
# )


import boto3
s3 = boto3.client('s3')

def main(input_path,model_path,scale,outscale):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='inputs', help='Input image or folder')
    parser.add_argument(
        '--model_path',
        type=str,
        default='experiments/pretrained_models/RealESRGAN_x4plus.pth',
        help='Path to the pre-trained model')
    parser.add_argument('--output', type=str, default='results', help='Output folder')
    parser.add_argument('--netscale', type=int, default=4, help='Upsample scale factor of the network')
    parser.add_argument('--outscale', type=float, default=4, help='The final upsampling scale of the image')
    parser.add_argument('--suffix', type=str, default='out', help='Suffix of the restored image')
    parser.add_argument('--tile', type=int, default=0, help='Tile size, 0 for no tile during testing')
    parser.add_argument('--tile_pad', type=int, default=10, help='Tile padding')
    parser.add_argument('--pre_pad', type=int, default=0, help='Pre padding size at each border')
    parser.add_argument('--half', action='store_true', help='Use half precision during inference')
    parser.add_argument(
        '--alpha_upsampler',
        type=str,
        default='realesrgan',
        help='The upsampler for the alpha channels. Options: realesrgan | bicubic')
    parser.add_argument(
        '--ext',
        type=str,
        default='auto',
        help='Image extension. Options: auto | jpg | png, auto means using the same extension as inputs')
    args,unknown = parser.parse_known_args()

    args.input = input_path
    args.model_path = model_path
    args.netscale = scale
    args.outscale  = outscale

    upsampler = RealESRGANer(
        scale=args.netscale,
        model_path=args.model_path,
        tile=args.tile,
        tile_pad=args.tile_pad,
        pre_pad=args.pre_pad,
        half=args.half)
    os.makedirs(args.output, exist_ok=True)
    if os.path.isfile(args.input):
        paths = [args.input]
    else:
        paths = sorted(glob.glob(os.path.join(args.input, '*')))

    for idx, path in enumerate(paths):
        imgname, extension = os.path.splitext(os.path.basename(path))
        print('Testing', idx, imgname)

        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        h, w = img.shape[0:2]
        if max(h, w) > 1000 and args.netscale == 4:
            import warnings
            warnings.warn('The input image is large, try X2 model for better performace.')
        if max(h, w) < 500 and args.netscale == 2:
            import warnings
            warnings.warn('The input image is small, try X4 model for better performace.')

        try:
            output, img_mode = upsampler.enhance(img, outscale=args.outscale)
        except Exception as error:
            print('Error', error)
        else:
            if args.ext == 'auto':
                extension = extension[1:]
            else:
                extension = args.ext
            if img_mode == 'RGBA':  # RGBA images should be saved in png format
                extension = 'png'
            save_path = os.path.join(args.output, f'{imgname}_{args.suffix}.{extension}')
            cv2.imwrite(save_path, output)



# @app.route('/')
# def home():
#     return render_template('index.html')

# @app.route('/super')
def supre_resolution(imageurl,scale_type):
    # imageurl = request.args.get('imageurl')
    # scale_type = request.args.get('type')

    # imageurl = "https://cdn.styldod.com/adobe_experiment/ext0_1619178332146.jpg"

    S = 10  # number of characters in the string.
    ran = ''.join(random.choices(string.ascii_uppercase + string.digits, k = S)) 
    unique_name =  str(ran)
    if(imageurl == None ):
        return {"error":"please provide url"}
 
    im = Image.open(requests.get(imageurl,stream=True).raw)
    width,height = im.size
    # Width/height check only for testing
    if(width > 2048 or height > 2048):
        if width >= height:
            new_w = 2048
            new_h = (new_w/width) * height
            im = im.resize((int(new_w),int(new_h)))
        else:
            new_h = 2048
            new_w = (new_h/height) * width
            im = im.resize((int(new_w),int(new_h)))
    #----------------------------------
    im = im.convert('RGB')
    im.save("./inputs/"+unique_name + ".jpg")
    input_path = "./inputs/"+unique_name + ".jpg"
    print(scale_type)
    if(scale_type == '4x'):
        model_path = "experiments/pretrained_models/RealESRGAN_x4plus.pth"
        scale = 4
        out_scale = 4
    elif(scale_type == '2x'):
        model_path = "experiments/pretrained_models/RealESRGAN_x2plus.pth"
        scale = 2
        out_scale =2
    else:
        #for 1x
        model_path = "experiments/pretrained_models/RealESRGAN_x2plus.pth"
        scale = 2
        out_scale =1
    
    main(input_path,model_path,scale,out_scale)
    torch.cuda.empty_cache()
    bucket_path = "adobe_experiment/aiml/" + unique_name+".jpg"
    output_path = "./results/"+ unique_name + "_out.jpg"
    # s3.Bucket('styldodassets').put_object(Key=s3key, Body=data,ACL="public-read")

    with open(output_path, 'rb') as f:
        s3.upload_fileobj(f, 'magicstore', bucket_path)

    print(bucket_path)
    os.remove("./results/" + unique_name +"_out.jpg")
    os.remove("./inputs/" + unique_name + ".jpg")
    resp = "https://magicstore.styldod.com/adobe_experiment/aiml/" + unique_name + ".jpg"
    

    return resp

# if __name__ == '__main__':
#     main()
