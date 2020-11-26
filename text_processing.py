# -*- coding: utf-8 -*-

from PIL import ImageFont

def split_longest_line(text, font, max_lines, draw, line_beg):
    arr = text.split('\n')
    max = 0;
    i = 0;
    index = 0;
    while i < len(arr):
        length = draw.textsize(arr[i], font)[0]
        if length > max:
            max = length
            index = i;
        i += 1;
    if " " not in arr[index][len(line_beg):].strip():
#        print("No space:   " + arr[index])
        return (False)
    else:
        if len(arr) > index + 1 and arr[index + 1][:len(line_beg)] == line_beg:
            i = arr[index][len(line_beg):].rfind(" ") + len(line_beg)
            new_str = arr[index][i + 1:]
            arr[index] = arr[index][:i]
            arr[index + 1] = line_beg + new_str + " " + arr[index + 1][len(line_beg):] 
        elif max_lines:
#            print("Max lines:   " + arr[index])
            return (False)
        else:
            mid = (len(arr[index]) + len(line_beg)) // 2
            a = arr[index][mid:].find(" ") + len(arr[index][:mid])
            b = arr[index][:mid].rfind(" ")
            i = a if a > b else b
            new_str = line_beg + arr[index][i + 1:]
            arr[index] = arr[index][:i]
            arr.insert(index + 1, new_str)
        text = '\n'.join(arr)
        return (text)

def handle_fontsize(text, width, height, font_path, fontsize, draw, line_beg):
    font = ImageFont.truetype(font_path, fontsize)
    (text_w, text_h) = draw.multiline_textsize(text[len(line_beg):], font)
    if text_h > height:
#        print ("text_h > height")
        return (False)
    if text_w <= width:
        return (text)        
    else:
        max_lines = False
        if draw.multiline_textsize(text[len(line_beg):] + "\nA", font)[1] > height:
#        if (fontsize + 2) * (len(text.split('\n')) + 1) > height:
            max_lines = True
#            print ((fontsize + 2) * (len(text.split('\n')) + 1), height)
#            print (text)
#            print (text.split('\n'))
        a = split_longest_line(text, font, max_lines, draw, line_beg)
        if not a:
#             print ("Not split longest line")
             return (False)
        else:
            text = a
            return (handle_fontsize(text, width, height, font_path, fontsize, draw, line_beg))

def process_text(text, width, height, font_path, fontsize, draw, line_beg):
#    a = handle_fontsize(text, width, height, font_path, fontsize, draw, line_beg)
#    while not a:
#        fontsize -= 2
#        a = handle_fontsize(text, width, height, font_path, fontsize, draw, line_beg)
#
    a = handle_fontsize(text, width, height, font_path, fontsize, draw, line_beg)
    if not a:
        mi = 4;
        ma = fontsize;
        while ma - mi > 1:
            if (ma - mi) % 2 == 0:
                mid = mi + (ma - mi) // 2
            else:
                mid = mi + (ma - mi) // 2 + 1
            a = handle_fontsize(text, width, height, font_path, mid, draw, line_beg)
            if not a:
                ma = mid
            else:
                mi = mid
        a = handle_fontsize(text, width, height, font_path, mi, draw, line_beg)
        fontsize = mi
    text = a
    font = ImageFont.truetype(font_path, fontsize)
    (text_w, text_h) = draw.multiline_textsize(text, font)
    return ({"text": text, "font": font, "width": text_w, "height": text_h})
