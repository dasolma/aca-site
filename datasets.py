import io
import os.path
import jinja2
import phm_datasets
from jinja2 import FileSystemLoader
from phm_datasets import datasets as phmd
import shutil
import random
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import imageio
import numpy as np

class HSLColor:
    def __init__(self, color_string):
        self.color_string = color_string
        self.hue = 0
        self.saturation = 0
        self.lightness = 0
        self.calculate_hsl()

    def calculate_hsl(self):
        if self.color_string.startswith("#") and len(self.color_string) == 7:
            r = int(self.color_string[1:3], 16) / 255
            g = int(self.color_string[3:5], 16) / 255
            b = int(self.color_string[5:7], 16) / 255
        else:
            return None

        max_val = max(r, g, b)
        min_val = min(r, g, b)
        h, s, l = 0, 0, (max_val + min_val) / 2

        if max_val == min_val:
            h = s = 0
        else:
            d = max_val - min_val
            s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
            if max_val == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_val == g:
                h = (b - r) / d + 2
            elif max_val == b:
                h = (r - g) / d + 4
            h /= 6

        self.hue = h * 360
        self.saturation = s * 100
        self.lightness = l * 100

    def to_hex_rgb(self):
        h = self.hue / 360
        s = self.saturation / 100
        l = self.lightness / 100

        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)

        to_hex = lambda c: format(int(c * 255), '02x')

        return f"#{to_hex(r)}{to_hex(g)}{to_hex(b)}"

def get_labels_colors(n):
    base_color = "#8A56E2"
    base_hue = HSLColor(base_color).hue

    colors = [HSLColor(base_color)]

    step = 240.0 / n

    for i in range(1, n):
        next_color = HSLColor(base_color)
        next_color.hue = (base_hue + step * i) % 240.0
        colors.append(next_color)

    return [color.to_hex_rgb() for color in colors]


# Example Usage:
color = HSLColor("#8A56E2")
print(f"Hue: {color.hue}, Saturation: {color.saturation}, Lightness: {color.lightness}")
print(f"Hex RGB: {color.to_hex_rgb()}")


def plot(values, filename, unit, feature, ntargets = None, target=None, target_label=None):

    color = 'blue'
    if target is not None:
        colors = get_labels_colors(ntargets)
        color = colors[target]

    max_size = 5000
    if values.shape[0] > max_size:
        frames = values.shape[0] // (max_size//2)

        with imageio.get_writer(filename + '.gif', mode='I', fps=2) as writer:
            for i in range(0, values.shape[0], max_size//2):
                fig = plt.figure(figsize=(16, 6))
                ax = fig.add_subplot(111)

                ax.plot(np.arange(i, i+max_size//2), values[i:i+max_size//2], c=color)
                if target_label is not None:
                    ax.set_title(f"{str(unit)} :: {feature} :: {target_label}")
                else:
                    ax.set_title(f"{str(unit)} :: {feature}")
                ax.set_ylim(values.min(), values.max())

                io_buf = io.BytesIO()
                fig.savefig(io_buf, format='raw')
                io_buf.seek(0)
                image = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
                                     newshape=(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1))
                io_buf.close()

                writer.append_data(image)
        return filename + '.gif'
    else:
        plt.figure(figsize=(16, 6))
        plt.plot(values)
        plt.title(f"{str(unit)} :: {feature}")
        plt.savefig(filename + '.svg')
        plt.cla()

        return filename + '.svg'

def render():

    if not os.path.exists('render/en/phm_datasets'):
        os.makedirs('render/en/phm_datasets')

    template_str = open('templates/dataset.html', 'r').read()
    environment = jinja2.Environment(loader=FileSystemLoader('templates'))

    for dataset in phmd.get_list():
        if dataset != 'AC16':
            continue

        meta = phmd.read_meta(dataset)
        meta['name'] = dataset

        # images
        for image in meta['system']['images']:
            shutil.copy(os.path.join(phm_datasets.__path__._path[0], 'datasets/images', image),
                        os.path.join('render/images/', image))

        # feature images
        meta['feature_images'] = []

        images_dir = f"render/images/{dataset}"
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

            dataname = meta['files'][0]['type']
            task_key = list(meta['tasks'].keys())[0]
            task = meta['tasks'][task_key]
            X = phmd.load(dataset, datasets=[dataname], unzip=True, task=task['target'])

            if isinstance(X, list) or isinstance(X, tuple):
                X = X[0]

            units = list(X[task['identifier']].drop_duplicates().values)
            if len(units) > 5:
                units = random.sample(units, 5)

            for unit in units:
                mask = X[task['identifier']] == unit
                mask = mask.values

                uname = '_'.join([str(e) for e in list(unit)])
                for feature in task['features']:
                    values = X.loc[mask, feature].values

                    ntargets, target, target_label = None, None, None
                    if task['type'] == "classification:multiclass":
                        ntargets = len(task['target_labels'])
                        target = X.loc[mask, task['target']].values[0]
                        target_label = task['target_labels'][target]
                    filename = plot(values, os.path.join(images_dir, f"u{str(uname)}_{feature}"),
                                    uname, feature, ntargets=ntargets, target=target, target_label=target_label)

                    meta['feature_images'].append(filename)
        else:
            for file in os.listdir(images_dir):
                meta['feature_images'].append(os.path.join(dataset, file))

        template = environment.from_string(template_str)
        content = template.render(meta)

        with open(os.path.join('render/en/phm_datasets', f'{dataset}.html'), 'w') as file:
            file.write(content)
            print(content)



