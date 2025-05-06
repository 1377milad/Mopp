import os
import cv2
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیمات اولیه
TOKEN = "8087872727:AAG6_Fy_SL6z-s_cJkojfihiBUVd-UfvSRM"  # توکن ربات خود را اینجا قرار دهید
VIDEO_DIR = "temp_videos"
OUTPUT_DIR = "processed_videos"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور شروع ربات"""
    await update.message.reply_text(
        "سلام! به ربات پردازش ویدیو خوش آمدید.\n"
        "یک ویدیو با سه کاسه ارسال کنید تا روی هر کاسه یک شکل (مربع, دایره, مثلث) قرار دهم.\n"
        "ویدیو باید شامل سه کاسه با پس زمینه نسبتاً ساده باشد."
    )

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش ویدیوی دریافتی"""
    if not update.message.video:
        await update.message.reply_text("لطفاً یک ویدیو ارسال کنید.")
        return

    # دریافت ویدیو
    video_file = await context.bot.get_file(update.message.video.file_id)
    input_path = os.path.join(VIDEO_DIR, f"input_{update.message.message_id}.mp4")
    await video_file.download_to_drive(input_path)

    # پردازش ویدیو
    output_path = os.path.join(OUTPUT_DIR, f"output_{update.message.message_id}.mp4")
    await process_video_with_shapes(input_path, output_path)

    # ارسال ویدیوی پردازش شده
    await update.message.reply_video(video=open(output_path, 'rb'), caption="ویدیوی پردازش شده با اشکال")

    # حذف فایل‌های موقت
    os.remove(input_path)
    os.remove(output_path)

async def process_video_with_shapes(input_path: str, output_path: str) -> None:
    """پردازش هر فریم ویدیو و اضافه کردن اشکال"""
    cap = cv2.VideoCapture(input_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # تنظیمات ویدیوی خروجی
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # تشخیص کاسه‌ها (با فرض کاسه‌های دایره‌ای)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 100,
            param1=50, param2=30, minRadius=50, maxRadius=200
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            circles = sorted(circles[0, :], key=lambda x: x[0])[:3]  # فقط سه کاسه اول
            
            for i, (x, y, r) in enumerate(circles):
                # اضافه کردن اشکال مختلف به هر کاسه
                if i == 0:  # کاسه اول - مربع
                    size = int(r * 0.7)
                    cv2.rectangle(frame, 
                                (x - size, y - size), 
                                (x + size, y + size), 
                                (0, 255, 0), 3)
                elif i == 1:  # کاسه دوم - دایره
                    cv2.circle(frame, (x, y), int(r * 0.6), (0, 0, 255), 3)
                elif i == 2:  # کاسه سوم - مثلث
                    pts = np.array([
                        [x, y - int(r * 0.6)],
                        [x - int(r * 0.6), y + int(r * 0.6)],
                        [x + int(r * 0.6), y + int(r * 0.6)]
                    ], np.int32)
                    cv2.polylines(frame, [pts], True, (255, 0, 0), 3)

        out.write(frame)

    cap.release()
    out.release()

def main() -> None:
    """اجرای ربات"""
    application = Application.builder().token(TOKEN).build()

    # مدیریت دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, process_video))

    # اجرای ربات
    application.run_polling()

if __name__ == '__main__':
    main()



