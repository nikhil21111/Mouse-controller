# create_icon.py - Programmatically draw a premium macOS app icon and compile to .icns

import os
import subprocess
from PIL import Image, ImageDraw, ImageFilter

def create_base_icon():
    # 1. Create a 1024x1024 high-resolution canvas
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 2. Draw a dark squircle (rounded rectangle) for macOS style icon
    # Margin to fit the macOS icon template
    margin = 80
    r = 180  # Corner radius
    
    # Outer background rounded box with a subtle gradient
    # We will draw a dark slate rounded box
    box_coords = [margin, margin, size - margin, size - margin]
    
    # Create gradient background
    for i in range(margin, size - margin):
        # Linear interpolation from dark purple-gray to dark navy-slate
        ratio = (i - margin) / (size - 2 * margin)
        r_val = int(15 + 15 * ratio)
        g_val = int(15 + 20 * ratio)
        b_val = int(22 + 25 * ratio)
        
        # Draw a horizontal line cropped by squircle mask
        # To keep it simple, we draw the rounded rect and layer a gradient mask
    
    # Simple solid dark background with rounded corners
    draw.rounded_rectangle(box_coords, radius=r, fill=(15, 16, 22, 255))
    
    # Subtle inner border for premium glassmorphic/native feel
    draw.rounded_rectangle(box_coords, radius=r, outline=(255, 255, 255, 20), width=6)

    # 3. Draw a glowing neon tracking target in the center
    center_x, center_y = size // 2, size // 2
    
    # Draw tracking grid/lines (representing coordinates)
    grid_color = (0, 122, 255, 40)  # Apple Blue, low opacity
    draw.line([center_x - 200, center_y, center_x + 200, center_y], fill=grid_color, width=4)
    draw.line([center_x, center_y - 200, center_x, center_y + 200], fill=grid_color, width=4)
    draw.ellipse([center_x - 120, center_y - 120, center_x + 120, center_y + 120], outline=grid_color, width=4)
    
    # Draw hand tracker mesh (cyberpunk joints theme)
    # We draw an index finger and thumb pinching, with glowing lines
    joint_color = (0, 255, 102, 255) # Neon Green
    line_color = (0, 255, 102, 100)
    
    # Finger coordinates
    wrist = (center_x - 100, center_y + 180)
    knuckle = (center_x - 50, center_y + 50)
    index_tip = (center_x + 50, center_y - 120)
    thumb_tip = (center_x + 120, center_y + 20)
    
    # Draw hand skeleton connections
    draw.line([wrist, knuckle, index_tip], fill=line_color, width=8)
    draw.line([knuckle, thumb_tip], fill=line_color, width=8)
    
    # Draw joints (circles)
    draw.ellipse([wrist[0]-15, wrist[1]-15, wrist[0]+15, wrist[1]+15], fill=joint_color)
    draw.ellipse([knuckle[0]-12, knuckle[1]-12, knuckle[0]+12, knuckle[1]+12], fill=joint_color)
    draw.ellipse([index_tip[0]-18, index_tip[1]-18, index_tip[0]+18, index_tip[1]+18], fill=joint_color)
    draw.ellipse([thumb_tip[0]-16, thumb_tip[1]-16, thumb_tip[0]+16, thumb_tip[1]+16], fill=joint_color)
    
    # Draw glowing active gesture indicator ring around index tip
    # We create a glowing ring using transparent ellipses
    glow_color = (0, 255, 102, 35)
    draw.ellipse([index_tip[0]-40, index_tip[1]-40, index_tip[0]+40, index_tip[1]+40], outline=glow_color, width=8)
    
    return img

def compile_icns():
    print("=== Generating macOS App Icon ===")
    base_img = create_base_icon()
    
    iconset_dir = "icon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    # Define required sizes for Apple Iconset
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png")
    ]
    
    # Save resized images to the iconset folder
    for size, name in sizes:
        resized_img = base_img.resize((size, size), Image.Resampling.LANCZOS)
        resized_img.save(os.path.join(iconset_dir, name))
        
    print("[+] Resized PNG icons created.")
    
    # Compile to .icns via Apple iconutil
    icns_path = "icon.icns"
    try:
        subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)
        print(f"[+] Compiled successfully: {icns_path}")
    except Exception as e:
        print(f"[-] iconutil compilation failed: {e}")
        
    # Clean up PNG iconset folder
    for _, name in sizes:
        try:
            os.remove(os.path.join(iconset_dir, name))
        except:
            pass
    try:
        os.rmdir(iconset_dir)
        print("[+] Cleaned up temporary iconset files.")
    except:
        pass

if __name__ == '__main__':
    compile_icns()
