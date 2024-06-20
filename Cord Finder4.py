import cv2 as cv
import numpy as np
import subprocess
import time
import os
import random
import PIL.Image as Image
import pytesseract as tess
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pyautogui as gui

# Configure Tesseract executable path
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Authenticate with Google Sheets API
sa = gspread.service_account(filename="service_account.json")
sh = sa.open("1960 Data")

ADB_PATH = r"C:\platform-tools\adb.exe"
device = "127.0.0.1:5575"

image_paths = {
    '093': r"C:\Cord Scanner\needles\coa_identifier\093.jpg",
    'f2p': r"C:\Cord Scanner\needles\coa_identifier\f2p.jpg",
    'sky': r"C:\Cord Scanner\needles\coa_identifier\sky.jpg",
    'db1': r"C:\Cord Scanner\needles\coa_identifier\db1.jpg",
    'fak': r"C:\Cord Scanner\needles\coa_identifier\fak.jpg",
    'fst': r"C:\Cord Scanner\needles\coa_identifier\fst.jpg",
    'oak': r"C:\Cord Scanner\needles\coa_identifier\oak.jpg",
    'cat': r"C:\Cord Scanner\needles\coa_identifier\cat.jpg",
    'b2w': r"C:\Cord Scanner\needles\coa_identifier\b2w.jpg",
    'db2': r"C:\Cord Scanner\needles\coa_identifier\db2.jpg",
    'O93': r"C:\Cord Scanner\needles\coa_identifier\O93.jpg",
    'cbg': r"C:\Cord Scanner\needles\coa_identifier\cbg.jpg",
    'city_identifier': r"C:\Cord Scanner\needles\CH25.jpg",
}

def cord_values(start_x=15, increment=8, iterations=100):
    original_cordsX = start_x
    for i in range(iterations):
        new_cordsX = original_cordsX + (i * increment)
        yield new_cordsX

def cord_changer(new_cordsX):
    adb_tap(530, 30)
    time.sleep(0.2)
    adb_tap(935, 214)
    time.sleep(1)
    adb_input_text(new_cordsX)
    time.sleep(1)
    adb_tap(1160, 217)
    time.sleep(1)
    adb_tap(1160, 217)
    time.sleep(1)
    adb_input_text(1185)
    time.sleep(1)
    adb_tap(1325, 212)
    time.sleep(1)
    adb_tap(1325, 212)

def adb_command(command):
    full_command = f'{ADB_PATH} -s {device} {command}'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, check=True)
        print(f"Executing {full_command}")
        print(result.stdout)
        print(result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing {full_command}: {e}")
        return None

def capture_screenshot(screenshot_path="/sdcard/screen.png", local_screenshot_dir="Screenshots"):
    local_screenshot_path = os.path.join(local_screenshot_dir, "screen.png")

    if not os.path.exists(local_screenshot_dir):
        os.makedirs(local_screenshot_dir)

    if adb_command(f'shell screencap -p {screenshot_path}') is None:
        print("Failed to capture screenshot")
        return None

    if adb_command(f'pull {screenshot_path} {local_screenshot_path}') is None:
        print("Failed to pull screenshot to local")
        return None

    print("Screenshot captured!")
    return local_screenshot_path

def find_image(template_path, threshold=0.6, screenshot_path=None):
    screenshot_path = capture_screenshot()
    
    if not os.path.exists(screenshot_path):
        print(f"Screenshot path does not exist: {screenshot_path}")
        return None

    haystack_img = cv.imread(screenshot_path, cv.IMREAD_ANYCOLOR)
    needle_img = cv.imread(template_path, cv.IMREAD_ANYCOLOR)

    if haystack_img is None:
        print(f"Failed to load haystack image: {screenshot_path}")
        return None

    if needle_img is None:
        print(f"Failed to load needle image: {template_path}")
        return None

    result = cv.matchTemplate(haystack_img, needle_img, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
    top_left = max_loc
    bottom_right = (top_left[0] + needle_img.shape[1], top_left[1] + needle_img.shape[0])

    if max_val >= threshold:
        x, y = max_loc
        print(f"Template matched with max value {max_val} at position ({x}, {y})")
        cv.rectangle(haystack_img, top_left, bottom_right, (0, 255, 0), 2)
        cv.imwrite("debug_match.png", haystack_img)
        return x, y
    
    print(f"No match found (max_val={max_val})")
    return None

def randomize_position(x, y, offset=0):
    return x + random.randint(-offset, offset), y + random.randint(-offset, offset)

def adb_tap(x, y, offset=1):
    random_x, random_y = randomize_position(x, y, offset)
    command = f'shell input tap {random_x} {random_y}'
    adb_command(command)
    print(f"Tapped at random position: ({random_x}, {random_y})")

def adb_swipe(x1, y1, x2, y2, duration=500):
    command = f'shell input swipe {x1} {y1} {x2} {y2} {duration}'
    adb_command(command)
    print(f"Swiped from ({x1}, {y1}) to ({x2}, {y2}) over {duration}ms")

def adb_input_text(text):
    command = f'shell input text "{text}"'
    adb_command(command)
    print(f"Typed text: {text}")

def connect_to_emulator():
    if adb_command(f'connect {device}'):
        return True
    else:
        adb_command('kill-server')
        adb_command('start-server')
        time.sleep(5)
        return adb_command(f'connect {device}') is not None

def image_find_use(identifier):
    template_path = image_paths.get(identifier)
    if template_path is None:
        print(f"Identifier {identifier} not found in image paths")
        return

    screenshot_path = capture_screenshot()
    position = find_image(template_path, screenshot_path=screenshot_path)
    
    if position:
        x, y = position
        adb_tap(x, y)
    else:
        print("Image not found in screenshot.")

def image_find_use2(identifier):
    template_path = image_paths.get(identifier)
    if template_path is None:
        print(f"Identifier {identifier} not found in image paths")
        return

    screenshot_path = capture_screenshot()
    position = find_image(template_path, screenshot_path=screenshot_path)
    
    if position:
        x, y = position
    else:
        print("Image not found in screenshot.")
        return
    y = (y-30)
    adb_tap(x, y)

def image_find_use_drag(identifier, x2, y2, duration=1000):
    template_path = image_paths.get(identifier)
    if template_path is None:
        print(f"Identifier {identifier} not found in image paths")
        return

    screenshot_path = capture_screenshot()
    position = find_image(template_path, screenshot_path=screenshot_path)
    
    if position:
        x1, y1 = position
        print(f"Dragging from ({x1}, {y1}) to ({x2}, {y2})")
        adb_swipe(x1, y1, x2, y2, duration)
    else:
        print("Image not found in screenshot.")
    time.sleep(1)
    adb_tap(960, 540)

def setup():
    time.sleep(1)
    adb_tap(90, 970)
    time.sleep(1)
    adb_tap(500, 50)
    time.sleep(1)
    adb_tap(950, 200)
    time.sleep(1)
    adb_input_text("15")
    time.sleep(1)
    adb_tap(1200, 200)
    time.sleep(1)
    adb_tap(1200, 200)
    adb_input_text("1185")
    time.sleep(1)
    adb_tap(1330, 200)
    adb_tap(1330, 200)
    time.sleep(2)
    zoom_out()
    time.sleep(3)
    print("Setup complete")

def zoom_out():
    gui.keyDown('s')
    time.sleep(0.3)
    gui.keyUp('s')

def intro():
    print("AFTER STARTING THE SCRIPT, YOU MUST CLICK BACK TO THE EMULATOR AND HOVER THE MOUSE NEAR THE CENTER OF THE SCREEN")
    print("")
    for seconds_till_start in range(5, 0, -1):
        time.sleep(1)
        print("Starting script in", seconds_till_start)

def extract_area(image_path, top_left, bottom_right, output_path):
    image = cv.imread(image_path)
    if image is None:
        print(f"Failed to load image: {image_path}")
        return None

    x1, y1 = top_left
    x2, y2 = bottom_right
    cropped_image = image[y1:y2, x1:x2]
    cv.imwrite(output_path, cropped_image)
    print(f"Cropped image saved to {output_path}")

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = tess.image_to_string(image)
    return text

def parse_profile_text(profile_text):
    lines = profile_text.split('\n')
    power, kill_points, alliance, coalition = '', '', '', ''
    for line in lines:
        line = line.strip()
        if line.startswith('Power'):
            power = line
        elif line.startswith('Kill Points'):
            kill_points = line
        elif line.startswith('Alliance'):
            alliance = line
        elif line.startswith('Coalition'):
            coalition = line
    return power, kill_points, alliance, coalition

def extract_and_send():
    profile_image_path = "C:/Cord Scanner/Screenshots/saved_img.png"
    profile_text = extract_text_from_image(profile_image_path)
    print(f"Profile text: {profile_text}")
    send_to_sheet(profile_text)

def send_to_sheet(profile_text):
    worksheet_name = "Sheet1"
    wks = sh.worksheet(worksheet_name)
    power, kill_points, alliance, coalition = parse_profile_text(profile_text)
    wks.update_acell("C2", power)
    wks.update_acell("D2", kill_points)
    wks.update_acell("E2", alliance)
    wks.update_acell("F2", coalition)
    print(f"Updated cell C2 with the value '{power}'")
    print(f"Updated cell D2 with the value '{kill_points}'")
    print(f"Updated cell E2 with the value '{alliance}'")
    print(f"Updated cell F2 with the value '{coalition}'")

def find_city_and_extract():
    example_img_path = r"C:\Cord Scanner\needles\entire_profile.jpg"
    saved_img_path = r"C:\Cord Scanner\Screenshots\saved_img.png"
    image_find_use2('093')
    time.sleep(2)
    position = find_image(example_img_path)
    
    if position:
        x, y = position
        width, height = 750, 450
        top_left = (x , y - 25)
        bottom_right = (x + width, y + height)
        screenshot_path = capture_screenshot()
        if screenshot_path:
            extract_area(screenshot_path, top_left, bottom_right, saved_img_path)
            print(f"Image found and area saved as {saved_img_path}")
        else:
            print("Failed to capture a new screenshot.")
    else:
        print("Example image not found in screenshot.")
    extract_and_send()

def main():
    time.sleep(1)
    zoom_out()
    time.sleep(3)
    for new_cordsX in cord_values():
        cord_changer(new_cordsX)
        time.sleep(2)
        find_city_and_extract()
    print("End")

if __name__ == "__main__":
    main()
