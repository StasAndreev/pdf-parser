import os
import shutil
import progressbar
from PyPDF4 import PdfFileReader, PdfFileWriter
from PIL import Image
import yaml
from marker.convert import convert_single_pdf
from marker.models import load_all_models
from marker.output import save_markdown
import fitz
from tqdm import tqdm
from functools import partialmethod

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)
TEMP_DIR = '$temp'
CONFIG_PATH = 'config.yml'

def write_status(file_path, status):
    """
    Updates contents of a status file
    :param file_path: path to the file
    :param status: value to write
    """
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(status))

def clear_file_paths(temp_dir, output_img, output_pages):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(f'{temp_dir}/pages', exist_ok=True)
    os.makedirs(f'{temp_dir}/marker', exist_ok=True)
    if os.path.exists(output_img):
        shutil.rmtree(output_img)
    os.makedirs(output_img, exist_ok=True)
    if os.path.exists(output_pages):
        shutil.rmtree(output_pages)
    os.makedirs(output_pages, exist_ok=True)

def read_langs(language_file):
    """
    Read languages from file
    :param language_file: file
    """
    with open(language_file, 'r') as file:
        text = file.read()
        return text.split(',')

def split_pages(file_path, output_directory):
    """
    Splits PDF into multiple single-page files
    :param file_path: path to source PDF
    :param output_directory: directory to where save the files
    :return: number of pages
    """
    with open(file_path, 'rb') as file:
        reader = PdfFileReader(file)
        num = reader.getNumPages()
        for page in range(num):
            reader = PdfFileReader(file)
            with open(f'{output_directory}/page{page}.pdf', 'wb') as page_file:
                writer = PdfFileWriter()
                writer.addPage(reader.getPage(page))
                writer.write(page_file)
        return num

def merge_markdown_pages(input_directory, output_file_directory, output_image_directory, num_pages):
    """
    Merges pages into single file and puts images into single directory
    :param input_directory: directory with page folders
    :param output_file_directory: directory with result file
    :param output_image_directory: directory with result images
    :param num_pages: amount of pages to process
    """
    open(f'{output_file_directory}/result.md', 'w', encoding='utf-8').close()
    with open(f'{output_file_directory}/result.md', 'a', encoding='utf-8') as outfile:
        for i in range(num_pages):
            files = os.listdir(f'{input_directory}/page{i}')
            pngs = [file for file in files if file.endswith('.png')]
            with open(f'{input_directory}/page{i}/page{i}.md', 'r', encoding='utf-8') as infile:
                content = infile.read()
                for png in pngs:
                    newname = f'{i}{png[1:]}'
                    shutil.copy(f'{input_directory}/page{i}/{png}', f'{output_image_directory}/{newname}')
                    content = content.replace(png, newname)
                outfile.write(f'<page_start>{i + 1}</page_start>\n')
                outfile.write(f'{content}\n')
                outfile.write(f'<page_end>{i + 1}</page_end>\n')

def compress_images(image_folder):
    """
    Compresses the images in given folder. Assumes directory only contains images
    :param image_folder: path to images
    """
    images = os.listdir(image_folder)
    for i in progressbar.progressbar(range(len(images))):
        im = Image.open(f'{image_folder}/{images[i]}')
        im.save(f'{image_folder}/{images[i]}', optimize=True, quality=80)

def transform_markdown(input_file, output_file):
    """
    Transforms md to xml
    :param input_file: md file
    :param output_file: xml file
    """
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            line = line[:-1]
            if line == '':
                continue
            if line.startswith('!'):
                filename = line[2:line.index(']', 2)]
                outfile.write(f'<image>{filename}</image>\n')
            elif line.startswith('$'):
                outfile.write(f'<formula>{line[2:-2]}</formula>\n')
            elif line.startswith('#'):
                trimmed_line = line.lstrip('#')
                i = len(line) - len(trimmed_line)
                outfile.write(f'<h{i}>{trimmed_line}</h{i}>\n')
            elif line.startswith('<'):
                outfile.write(f'{line}\n')
            else:
                outfile.write(f'<p>{line}</p>\n')

def save_pdf_as_image(input_file, output_folder):
    """
    Extracts pdf pages in png format
    :param input_file: PDF file
    :param output_folder: result folder for png pages
    """
    with open(input_file, 'rb') as file:
        reader = PdfFileReader(file)
        num = reader.getNumPages()
    pdf = fitz.open(input_file)
    for i in progressbar.progressbar(range(num)):
        page = pdf.load_page(i)
        pix = page.get_pixmap()
        os.makedirs(f'{output_folder}', exist_ok=True)
        pix.save(f'{output_folder}/page{i}.png')


def contents(file):
    with open(file, 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    try:
        yaml = yaml.safe_load(open(CONFIG_PATH, encoding='utf-8'))
        write_status(yaml['StatusFile'], 1)
        INPUT_FILE = contents(yaml['InputFile'])
        OUTPUT_FILE_FOLDER = yaml['OutputFileFolder']
        OUTPUT_IMAGE_FOLDER = yaml['OutputImageFolder']
        OUTPUT_PAGES_FOLDER = yaml['OutputPagesFolder']
        LANGS = read_langs(yaml['LangFile'])
        clear_file_paths(TEMP_DIR, OUTPUT_IMAGE_FOLDER, OUTPUT_PAGES_FOLDER)
        print('Extracting PDF pages...')
        num_pages = split_pages(file_path=INPUT_FILE, output_directory=f'{TEMP_DIR}/pages')
        print('Loading marker...')
        model_list = load_all_models()
        print('Processing pages...')
        for i in progressbar.progressbar(range(num_pages)):
            full_text, images, meta = convert_single_pdf(f'{TEMP_DIR}/pages/page{i}.pdf', model_list, max_pages=1, langs=LANGS, batch_multiplier=1)
            os.makedirs(f'{TEMP_DIR}/marker/page{i}', exist_ok=True)
            save_markdown(f'{TEMP_DIR}/marker', f'page{i}.md', full_text, images, meta)
        print('Merging processed pages...')
        merge_markdown_pages('$temp/marker', OUTPUT_FILE_FOLDER, OUTPUT_IMAGE_FOLDER, num_pages)
        transform_markdown(f'{OUTPUT_FILE_FOLDER}/result.md', f'{OUTPUT_FILE_FOLDER}/result.xml')
        print('Compressing images...')
        compress_images(f'{OUTPUT_IMAGE_FOLDER}')
        print('Saving PDF as images...')
        save_pdf_as_image(INPUT_FILE, OUTPUT_PAGES_FOLDER)
        print('Compressing PDF images...')
        compress_images(OUTPUT_PAGES_FOLDER)
        write_status(yaml['StatusFile'], 2)
    except Exception as e:
        print(e)
        write_status(yaml['StatusFile'], 3)