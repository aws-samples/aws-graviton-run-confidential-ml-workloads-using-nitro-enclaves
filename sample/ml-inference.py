import os
import io
import argparse
import numpy as np
from PIL import Image
import onnx
from onnx_tf.backend import prepare


def process_command():
    parser = argparse.ArgumentParser(prog='Image Classifier')
    subparsers = parser.add_subparsers(help='Choose command')

    # parser for "classify" command
    parser_sync = subparsers.add_parser('classify', help='Use ML inference to classify image file using ResNet50')
    parser_sync.add_argument(
        '-m',
        '--model',
        type=str,
        help='Provide the ML model for image classification'
    )
    parser_sync.add_argument(
        '-l',
        '--labels',
        type=str,
        help='Provide the labels file for the ML model'
    )
    parser_sync.add_argument(
        '-d',
        '--dataset',
        type=str,
        help='Provide a directory with image files to classify'
    )
    parser_sync.add_argument(
        '-o',
        '--output',
        type=str,
        help='Provide an output directory to store results'
    )
    parser_sync.set_defaults(func=classify)

    args = parser.parse_args()
    args.func(args)


def softmax(x):
    exp_x = np.exp(x - np.max(x))
    return exp_x / exp_x.sum(axis=0)


def load_labels(label_file):
    with open(label_file, 'r') as f:
        labels = [label.rstrip() for label in f]
        return labels


def preprocess(img):
    with open(img, mode='rb') as fh:
        data = fh.read()

    img = Image.open(io.BytesIO(data))
    img = img.resize((256, 256), Image.Resampling.BILINEAR)
    img = img.crop((16, 16, 240, 240))
    img = img.convert('RGB')
    img = np.array(img).astype(np.float32)

    mean = np.array([0.485, 0.456, 0.406])
    stddev = np.array([0.229, 0.224, 0.225])
    img = ((img / 255.0) - mean) / stddev

    img = np.expand_dims(img, 0)
    img = np.transpose(img, [0, 3, 1, 2]).astype(np.float32)

    return img


def postprocess(scores):
    scores = np.squeeze(scores)
    return softmax(scores)


def top_class(N, probs, labels):
    results = np.argsort(probs)[::-1]

    classes = []
    for i in range(N):
        item = results[i]
        classes.append({
            "class": labels[item],
            "prob": float(probs[item])
        })

    return classes


def classify(args):
    dataset = args.dataset
    responses = {}

    model = onnx.load(args.model)

    for filename in os.listdir(dataset):
        if filename.endswith(".jpg"):
            image = os.path.join(dataset, filename)
            input = preprocess(image)

            scores = prepare(model).run(input)
            probs = postprocess(scores)

            labels = load_labels(args.labels)
            response = top_class(5, probs, labels)

            responses[filename] = response

    try:
        with open(args.output + "results.txt", 'w') as fh:
            fh.write(str(responses))
    except Exception:
        raise Exception(f"Error. Could not write file: results.txt.")


def main():
    process_command()


if __name__ == '__main__':
    main()
