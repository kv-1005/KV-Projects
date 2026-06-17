from PIL import Image
import collections

def get_actual_colors(image_path, num_colors=10):
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize((200, 200))
    pixels = list(img.getdata())
    
    # Filter out white and near-white colors
    filtered_pixels = [p for p in pixels if not (p[0] > 240 and p[1] > 240 and p[2] > 240)]
    
    color_counts = collections.Counter(filtered_pixels)
    most_common = color_counts.most_common(num_colors)
    return most_common

if __name__ == "__main__":
    logo_path = r"g:\MD Invoice\md logo.jpg"
    try:
        colors = get_actual_colors(logo_path)
        print("Actual branding colors (RGB):")
        for color, count in colors:
            hex_color = '#{:02x}{:02x}{:02x}'.format(*color)
            print(f"{hex_color}: {count}")
    except Exception as e:
        print(f"Error: {e}")
