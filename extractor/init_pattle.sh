#mkdir data_model
cd inference
data_det=https://paddleocr.bj.bcebos.com/20-09-22/server/det/ch_ppocr_server_v1.1_det_infer.tar
data_cls=https://paddleocr.bj.bcebos.com/20-09-22/cls/ch_ppocr_mobile_v1.1_cls_infer.tar
data_rec=https://paddleocr.bj.bcebos.com/20-09-22/server/rec/ch_ppocr_server_v1.1_rec_infer.tar
# 下载检测模型并解压
wget ${data_det} && tar xf ${data_det}
# 下载识别模型并解压
wget ${data_cls} && tar xf ${data_cls}
# 下载方向分类器模型并解压
wget ${data_rec} && tar xf ${data_rec}
cd ..

hub serving start -m chinese_ocr_db_crnn_mobile -p 8866

pip install paddlehub
pip install shapely
pip install pyclipper
pip install paddleocr


hub install chinese_ocr_db_crnn_server==1.1.0