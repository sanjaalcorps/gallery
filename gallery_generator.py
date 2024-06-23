import os
import json
from PIL import Image
import shutil
from jinja2 import Environment, FileSystemLoader
import random
import math
from datetime import datetime
import yaml

# Configuration
CONFIG_FILE = 'config.yaml'
with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

SOURCE_DIR = config['source_dir']
OUTPUT_DIR = config['output_dir']
THUMBNAIL_SIZE = tuple(config['thumbnail_size'])
ITEMS_PER_PAGE = config['items_per_page']
TEMPLATES_DIR = config['templates_dir']
STATIC_DIR = config['static_dir']

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def create_thumbnail(image_path, thumb_path):
    with Image.open(image_path) as img:
        img.thumbnail(THUMBNAIL_SIZE)
        img.save(thumb_path)

def get_image_size(image_path):
    with Image.open(image_path) as img:
        return f"{img.width}x{img.height}"

def process_images(album_path):
    album_name = os.path.basename(album_path)
    images = []
    thumbnail_dir = os.path.join(OUTPUT_DIR, 'thumbnails', album_name)
    os.makedirs(thumbnail_dir, exist_ok=True)

    for filename in os.listdir(album_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_path = os.path.join(album_path, filename)
            thumb_path = os.path.join(thumbnail_dir, filename)
            
            create_thumbnail(image_path, thumb_path)
            
            # Example tags, you can modify this to read from a file or metadata
            tags = ['tag1', 'tag2', 'tag3'] if filename.endswith('.jpg') else ['tag4', 'tag5']
            
            images.append({
                'filename': filename,
                'thumbnail': f"thumbnails/{album_name}/{filename}",
                'full_image': f"images/{album_name}/{filename}",
                'size': get_image_size(image_path),
                'tags': tags
            })
    
    return images

def generate_album_pages(album_name, images):
    template = env.get_template('album.html')
    total_pages = math.ceil(len(images) / ITEMS_PER_PAGE)
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_images = images[start_idx:end_idx]
        
        html = template.render(
            album_name=album_name,
            images=page_images,
            current_page=page,
            total_pages=total_pages,
            config=config,
            current_date=datetime.now().strftime("%B %d, %Y"),
            random_quote=random.choice(config['quotes'])
        )
        
        filename = f"{album_name}_page{page}.html" if page > 1 else f"{album_name}.html"
        with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
            f.write(html)

def generate_index_pages(albums):
    template = env.get_template('index.html')
    total_pages = math.ceil(len(albums) / ITEMS_PER_PAGE)
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_albums = albums[start_idx:end_idx]
        
        html = template.render(
            albums=page_albums,
            current_page=page,
            total_pages=total_pages,
            config=config,
            current_date=datetime.now().strftime("%B %d, %Y"),
            random_quote=random.choice(config['quotes'])
        )
        
        filename = f"index_page{page}.html" if page > 1 else "index.html"
        with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
            f.write(html)

def generate_search_pages(tag, images):
    try:
        template = env.get_template('search.html')
    except jinja2.exceptions.TemplateNotFound:
        print(f"Failed to load search.html. Available templates: {env.list_templates()}")
        return  # or raise an exception

    total_pages = math.ceil(len(images) / ITEMS_PER_PAGE)
    
    for page in range(1, total_pages + 1):
        start_idx = (page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_images = images[start_idx:end_idx]
        
        html = template.render(
            tag=tag,
            images=page_images,
            current_page=page,
            total_pages=total_pages,
            config=config,
            current_date=datetime.now().strftime("%B %d, %Y"),
            random_quote=random.choice(config['quotes'])
        )
        
        filename = f"search_{tag}_page{page}.html" if page > 1 else f"search_{tag}.html"
        with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
            f.write(html)


def generate_json(albums):
    with open(os.path.join(OUTPUT_DIR, "gallery.json"), 'w') as f:
        json.dump(albums, f, indent=2)

def copy_static_files():
    shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, 'static'), dirs_exist_ok=True)

def main():
    albums = []
    tag_map = {}
    
    for album_name in os.listdir(SOURCE_DIR):
        album_path = os.path.join(SOURCE_DIR, album_name)
        if os.path.isdir(album_path):
            print(f"Processing album: {album_name}")
            images = process_images(album_path)
            
            albums.append({
                'name': album_name,
                'images': images,
                'thumbnail': random.choice(images)['thumbnail'] if images else ''
            })
            
            for image in images:
                for tag in image['tags']:
                    if tag not in tag_map:
                        tag_map[tag] = []
                    tag_map[tag].append(image)
            
            generate_album_pages(album_name, images)
            
            # Copy original images to output directory
            output_album_dir = os.path.join(OUTPUT_DIR, 'images', album_name)
            os.makedirs(output_album_dir, exist_ok=True)
            for image in images:
                shutil.copy2(
                    os.path.join(album_path, image['filename']),
                    os.path.join(output_album_dir, image['filename'])
                )
    
    generate_index_pages(albums)
    generate_json(albums)
    copy_static_files()
    
    for tag, images in tag_map.items():
        generate_search_pages(tag, images)
    
    print("Gallery generation complete!")

if __name__ == "__main__":
    main()