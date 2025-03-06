# -*- coding: utf-8 -*-
# @Time    : 2025/2/27 下午7:44
# @Author  : wm
# @Software   : PyCharm
"""
在一次淹没模拟后，接收一个(x, y)坐标对
根据这个坐标对找到对应网格开始淹没的时刻
然后找到对应时刻的佛子岭、磨子潭、白莲崖坝下水位返回
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from loguru import logger
from config import *
from CoordHandler import CoordHandler

app = Flask(__name__)

# Enable CORS for the entire app
CORS(app)


@app.route('/find_water_depth', methods=['post'])
def find_water_depth():
    try:
        x = request.json['longitude']
        y = request.json['latitude']
        # 检查是否为经纬度
        if not (-90.0 <= float(y) <= 90.0):
            raise Exception
        if not (-180 <= float(x) <= 180.0):
            raise Exception
        logger.info("JSON信息解析完成")
    except Exception as e:
        logger.error(e)
        return "Failed: JSON信息解析失败，请检查经纬度的格式后重试！"

    try:
        coord_handler = CoordHandler(RESULT_PATH)
        coord_handler.check_finish()
        fid = coord_handler.find_grid_id(float(x), float(y))
        row_index = coord_handler.find_flooding(fid)
        values = coord_handler.find_dam_water_depth(row_index)
        logger.info("坝下水位提取成功！")
    except Exception as e:
        logger.error(e)
        return "Failed: 坝下水位提取过程中出现错误"

    return values


if __name__ == '__main__':
    # 调试时用这行代码启动服务器
    app.run(host="0.0.0.0", port=19998, debug=False)
