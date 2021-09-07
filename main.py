import os
import re
import cv2
import argparse
from tqdm import tqdm

parser = argparse.ArgumentParser(description='動画フレーム間差分')

parser.add_argument('--input', help='入力ファイルパス', required=True)
parser.add_argument('--show', help='表示フラグ', action='store_true')

parser.add_argument('--out_dir', help='出力ディレクトリ', default='./')
parser.add_argument('--out_movie', help='動画出力場所')
parser.add_argument('--out_file', help='分割ファイルの出力設定', type=bool)
parser.add_argument('--out_size', help='動画サイズ')
parser.add_argument('--movie_extension', help='動画ファイル拡張子', default='mp4')
parser.add_argument('--img_extension', help='画像ファイル拡張子', default='png')

args = parser.parse_args()


def calc_black_whiteArea(bw_image):
    image_size = bw_image.size
    whitePixels = cv2.countNonZero(bw_image)
    blackPixels = bw_image.size - whitePixels

    whiteAreaRatio = (whitePixels / image_size) * 100  # [%]
    blackAreaRatio = (blackPixels / image_size) * 100  # [%]

    return whiteAreaRatio, blackAreaRatio


def img_diff(prev_image, next_image):
    gray_prev_img = cv2.cvtColor(prev_image, cv2.COLOR_BGR2GRAY)
    gray_next_img = cv2.cvtColor(next_image, cv2.COLOR_BGR2GRAY)

    mask = cv2.absdiff(gray_next_img, gray_prev_img)
    return mask


def movie_diff(args, movie_path):
    # 動画ファイルのキャプチャ
    cap = cv2.VideoCapture(movie_path)

    # 最初のフレームを背景画像に設定
    ret, bg = cap.read()

    # フレーム総数の取得
    total_frame = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    if args.out_dir is not None:
        os.makedirs(args.out_dir, exist_ok=True)

    if args.out_movie is not None:
        fmt = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')  # ファイル形式(ここではmp4)
        video_writer = cv2.VideoWriter(f'{args.out_dir}/{args.out_movie}.{args.movie_extension}',
                                       fmt,
                                       int(cap.get(cv2.CAP_PROP_FPS)),
                                       (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                        int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))  # ライター作成

    for i in tqdm(range(total_frame - 1)):
        ret, frame = cap.read()

        if not ret:
            break

        # 画像差分
        mask = img_diff(bg, frame)

        # 差分画像を二値化してマスク画像を算出
        thresh = cv2.threshold(mask, 30, 255, cv2.THRESH_BINARY)[1]

        whiteAreaRatio, blackAreaRatio = calc_black_whiteArea(thresh)

        cv2.rectangle(thresh, (0, 0), (int(W / 2), 30), (255, 255, 255), thickness=-1)
        cv2.putText(thresh, f'while : {str(whiteAreaRatio)} - brack : {str(blackAreaRatio)}',
                    (0, 30), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 0), lineType=cv2.LINE_AA)

        # フレームとマスク画像を表示
        if args.show:
            cv2.imshow("Mask", thresh)
            # qキーが押されたら途中終了
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if args.out_movie is not None:
            video_writer.write(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))

        if args.out_file:
            digit = len(str(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))))
            file_name = re.split(r"[/\\.]", movie_path)
            cv2.imwrite(f'{args.out_dir}/{file_name[-2]}_{str(i).zfill(digit)}.{args.img_extension}', thresh)

        # 比較元フレームの更新
        bg = frame

    if args.out_movie is not None:
        video_writer.release()


def main(args):
    input_path = args.input
    movie_diff(args, input_path)


if __name__ == '__main__':
    main(args)
