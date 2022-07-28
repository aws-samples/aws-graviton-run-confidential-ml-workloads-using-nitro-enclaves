import os
import json
import argparse
import numpy as np
import tensorflow as tf


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


def postprocess(scores):
    scores = np.squeeze(scores)
    return softmax(scores)


def load_labels(label_file):
    with open(label_file, 'r') as f:
        labels = json.load(f)
        return labels


def preprocess(img):
    img = tf.keras.preprocessing.image.load_img(img, target_size=(224, 224))
    img = tf.keras.preprocessing.image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = tf.keras.applications.resnet50.preprocess_input(img)

    return img


def top_class(N, probs, labels):
    results = np.argsort(probs)[::-1]

    classes = []
    for i in range(N):
        classes.append({
            "class": labels[str(results[i])][1],
            "prob": float(probs[int(results[i])])
        })

    return classes


def classify(args):
    dataset = args.dataset
    responses = {}

    model = tf.keras.applications.resnet.ResNet50(
        include_top=True,
        weights=args.model,
        input_tensor=None,
        input_shape=None
    )

    for filename in os.listdir(dataset):
        if filename.endswith(".jpg"):
            image = os.path.join(dataset, filename)
            input_data = preprocess(image)

            scores = model.predict(input_data)
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
