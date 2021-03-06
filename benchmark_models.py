"""Compare speed of different models"""
"""Code from https://github.com/ryujaehun/pytorch-gpu-benchmark"""
"""Add options to use PyTorch Profiler"""

import torch
import torchvision.models as models
import platform
import psutil
import torch.nn as nn
import datetime
import time
import os
import pandas as pd
import argparse
from torch.utils.data import Dataset, DataLoader
import json
from pathlib import Path


torch.backends.cudnn.benchmark = True
# https://discuss.pytorch.org/t/what-does-torch-backends-cudnn-benchmark-do/5936
# This flag allows you to enable the inbuilt cudnn auto-tuner to find the best algorithm to use for your hardware.
# If you check it using the profile tool, the cnn method such as winograd, fft, etc. is used for the first iteration and the best operation is selected for the device.


MODEL_LIST = {
    models.vgg: models.vgg.__all__[1:],
    models.resnet: models.resnet.__all__[1:],
    # models.mobilenet: models.mobilenet.mv2_all[1:],
    # models.mobilenet: models.mobilenet.mv3_all[1:],
    # models.mnasnet: models.mnasnet.__all__[1:],
    # models.densenet: models.densenet.__all__[1:],
    # models.squeezenet: models.squeezenet.__all__[1:],
    # models.shufflenetv2: models.shufflenetv2.__all__[1:],
}

black_list = ["resnext101_32x8d"]

# For post-voltaic architectures, there is a possibility to use tensor-core at half precision.
# Due to the gradient overflow problem, apex is recommended for practical use.
device_name = str(torch.cuda.get_device_name(0))
# Training settings
parser = argparse.ArgumentParser(description="PyTorch Benchmarking")
parser.add_argument("--WARM_UP", "-w", type=int, default=5, required=False, help="Num of warm up")
parser.add_argument("--NUM_TEST", "-n", type=int, default=10, required=False, help="Num of Test")
parser.add_argument(
    "--BATCH_SIZE", "-b", type=int, default=8, required=False, help="Num of batch size"
)
parser.add_argument(
    "--NUM_CLASSES", "-c", type=int, default=1000, required=False, help="Num of class"
)
parser.add_argument("--NUM_GPU", "-g", type=int, default=1, required=False, help="Num of gpus")
parser.add_argument(
    "--folder", "-f", type=str, default="result", required=False, help="folder to save results"
)
parser.add_argument(
    "--precision", "-p", type=str, default="float", choices=["float", "half", "double"], help="Precision to run the benchmark")
parser.add_argument(
    '--use_profiler', action="store_true", default=None, help="Flag to turn on profiler.")

args = parser.parse_args()
args.BATCH_SIZE *= args.NUM_GPU


class RandomDataset(Dataset):
    def __init__(self, length):
        self.len = length
        self.data = torch.randn(3, 224, 224, length)

    def __getitem__(self, index):
        return self.data[:, :, :, index]

    def __len__(self):
        return self.len


rand_loader = DataLoader(
    dataset=RandomDataset(args.BATCH_SIZE * (args.WARM_UP + args.NUM_TEST)),
    batch_size=args.BATCH_SIZE,
    shuffle=False,
    num_workers=8,
)


def train_steps(model, precision, criterion, target, profiler=None):
    durations = []
    for step, img in enumerate(rand_loader):
        img = getattr(img, precision)()
        torch.cuda.synchronize()
        start = time.time()
        model.zero_grad()
        prediction = model(img.to("cuda"))
        loss = criterion(prediction, target)
        loss.backward()
        torch.cuda.synchronize()
        end = time.time()
        if profiler:
            profiler.step()
        if step >= args.WARM_UP:
            durations.append((end - start) * 1000)
    return durations


def train(precision="float", profile=False):
    """use fake image for training speed test"""
    target = torch.LongTensor(args.BATCH_SIZE).random_(args.NUM_CLASSES).cuda()
    criterion = nn.CrossEntropyLoss()
    benchmark = {}
    for model_type in MODEL_LIST.keys():
        for model_name in MODEL_LIST[model_type]:
            if model_name not in black_list:
                model = getattr(model_type, model_name)(pretrained=False)
                if args.NUM_GPU > 1:
                    model = nn.DataParallel(model, device_ids=range(args.NUM_GPU))
                model = getattr(model, precision)()
                model = model.to("cuda")
                
                print(f"Benchmarking Training {precision} precision type {model_name} ")

                if profile:
                    path_log = './' + args.folder + '/' + model_name + '/train/' + precision + '/stack_memory'
                    Path(path_log).mkdir(parents=True, exist_ok=True)
                    with torch.profiler.profile(
                        activities=[
                            torch.profiler.ProfilerActivity.CPU,
                            torch.profiler.ProfilerActivity.CUDA],
                        schedule=torch.profiler.schedule(
                            wait=0, # skip first few training steps
                            warmup=args.WARM_UP, # reach steady and skip few layers, profiling happens ignores results
                            active=args.NUM_TEST), # only profile NUM_TEST steps - allows to focus and skip some layers for reducing overhead(even in prod)
                        on_trace_ready=torch.profiler.tensorboard_trace_handler(path_log),
                        record_shapes=True,
                        profile_memory=True,
                        with_stack=True
                    ) as p:
                        durations = train_steps(model, precision, criterion, target, p)
                else:
                    durations = train_steps(model, precision, criterion, target)
                
                del model
                benchmark[model_name] = durations
                print(f"{model_name} model average train time : {sum(durations)/len(durations)}ms")

    return benchmark


def inference_steps(model, precision, profiler=None):
    durations = []
    for step, img in enumerate(rand_loader):
        img = getattr(img, precision)()
        torch.cuda.synchronize()
        start = time.time()
        model(img.to("cuda"))
        torch.cuda.synchronize()
        end = time.time()
        if profiler:
            profiler.step()
        if step >= args.WARM_UP:
            durations.append((end - start) * 1000)
    return durations


def inference(precision="float", profile=False):
    benchmark = {}
    with torch.no_grad():
        for model_type in MODEL_LIST.keys():
            for model_name in MODEL_LIST[model_type]:
                if model_name not in black_list:
                    model = getattr(model_type, model_name)(pretrained=False)
                    if args.NUM_GPU > 1:
                        model = nn.DataParallel(model, device_ids=range(args.NUM_GPU))
                    model = getattr(model, precision)()
                    model = model.to("cuda")
                    model.eval()
                    
                    print(f"Benchmarking Inference {precision} precision type {model_name} ")

                    if profile:
                        path_log = './' + args.folder + '/' + model_name + '/inference/' + precision + '/stack_memory'
                        Path(path_log).mkdir(parents=True, exist_ok=True)
                        with torch.profiler.profile(
                            activities=[
                                torch.profiler.ProfilerActivity.CPU,
                                torch.profiler.ProfilerActivity.CUDA],
                            schedule=torch.profiler.schedule(
                                wait=0, # skip first few training steps
                                warmup=args.WARM_UP, # reach steady and skip few layers, profiling happens ignores results
                                active=args.NUM_TEST), # only profile NUM_TEST steps - allows to focus and skip some layers for reducing overhead(even in prod)
                            on_trace_ready=torch.profiler.tensorboard_trace_handler(path_log),
                            record_shapes=True,
                            profile_memory=True,
                            with_stack=True
                        ) as p:
                            durations = inference_steps(model, precision, p)
                    else:
                        durations = inference_steps(model, precision)

                    del model
                    benchmark[model_name] = durations
                    print(f"{model_name} model average inference time : {sum(durations)/len(durations)}ms")
                
    return benchmark


f"{platform.uname()}\n{psutil.cpu_freq()}\ncpu_count: {psutil.cpu_count()}\nmemory_available: {psutil.virtual_memory().available}"


if __name__ == "__main__":
    folder_name = args.folder

    device_name = f"{device_name}_{args.NUM_GPU}_gpus_"
    system_configs = f"{platform.uname()}\n\
                     {psutil.cpu_freq()}\n\
                    cpu_count: {psutil.cpu_count()}\n\
                    memory_available: {psutil.virtual_memory().available}"
    gpu_configs = [
        torch.cuda.device_count(),
        torch.version.cuda,
        torch.backends.cudnn.version(),
        torch.cuda.get_device_name(0),
    ]
    gpu_configs = list(map(str, gpu_configs))
    temp = [
        "Number of GPUs on current device : ",
        "CUDA Version : ",
        "Cudnn Version : ",
        "Device Name : ",
    ]

    os.makedirs(folder_name, exist_ok=True)
    with open(os.path.join(folder_name, "config.json"), "w") as f:
        json.dump(vars(args), f, indent=2)
    now = datetime.datetime.now()

    start_time = now.strftime("%Y/%m/%d %H:%M:%S")

    print(f"benchmark start : {start_time}")

    for idx, value in enumerate(zip(temp, gpu_configs)):
        gpu_configs[idx] = "".join(value)
        print(gpu_configs[idx])
    print(system_configs)

    with open(os.path.join(folder_name, "system_info.txt"), "w") as f:
        f.writelines(f"benchmark start : {start_time}\n")
        f.writelines("system_configs\n\n")
        f.writelines(system_configs)
        f.writelines("\ngpu_configs\n\n")
        f.writelines(s + "\n" for s in gpu_configs)

        train_result = train(args.precision, args.use_profiler)
        train_result_df = pd.DataFrame(train_result)
        path = f"{folder_name}/{device_name}_{args.precision}_model_train_benchmark.csv"
        train_result_df.to_csv(path, index=False)

        inference_result = inference(args.precision, args.use_profiler)
        inference_result_df = pd.DataFrame(inference_result)
        path = f"{folder_name}/{device_name}_{args.precision}_model_inference_benchmark.csv"
        inference_result_df.to_csv(path, index=False)

    now = datetime.datetime.now()

    end_time = now.strftime("%Y/%m/%d %H:%M:%S")
    print(f"benchmark end : {end_time}")
    with open(os.path.join(folder_name, "system_info.txt"), "a") as f:
        f.writelines(f"benchmark end : {end_time}\n")
