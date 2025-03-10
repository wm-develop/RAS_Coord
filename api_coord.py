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
        fid = request.json['FID']
        # 类型和数值验证
        if isinstance(fid, int):
            pass  # 直接进入范围判断
        elif isinstance(fid, float):
            # 允许整数形式的浮点数（如3.0）
            if not fid.is_integer():
                raise ValueError()
            fid = int(fid)  # 转换为整数类型
        else:
            # 非数字或浮点非整数情况
            raise ValueError()

        # 范围验证
        if not (0 <= fid <= 35807):
            raise ValueError()

        logger.info("网格编号读取成功")

    except KeyError:
        logger.error(KeyError)
        return jsonify({"error": "请求JSON中没有FID字段"}), 400
    except ValueError:
        logger.error(ValueError)
        return jsonify({"error": "FID必须为0-35807之间的整数"}), 400
    except Exception as e:
        logger.error(e)
        return jsonify({"error": "请求格式不正确"}), 400

    try:
        coord_handler = CoordHandler(RESULT_PATH)
        coord_handler.read_shapefile()
        logger.info("网格shp文件读取成功")
    except RuntimeError:
        logger.error(RuntimeError)
        return jsonify({"error": str(RuntimeError)}), 404

    try:
        coord_handler.check_finish()
        logger.info("已完成文件完整性校验")
    except RuntimeError as e:
        logger.error(e)
        return jsonify({"error": str(RuntimeError)}), 404

    try:
        row_index = coord_handler.find_flooding(fid)
        values = coord_handler.find_dam_water_depth(row_index)
        logger.info("坝下水位提取成功")
    except KeyError as ke:
        logger.error(ke)
        return jsonify({"error": str(ke)}), 404
    except RuntimeError as re:
        logger.error(re)
        return jsonify({"error": str(re)}), 404
    except AssertionError as ae:
        logger.error(ae)
        return jsonify({"error": str(ae)}), 404
    except IndexError as ie:
        logger.error(ie)
        return jsonify({"error": str(ie)}), 404

    return jsonify({
        "status": "success",
        "data": {
            "fzl": values[0],
            "bly": values[1],
            "mzt": values[2]
        }
    })


if __name__ == '__main__':
    # 调试时用这行代码启动服务器
    app.run(host="0.0.0.0", port=19998, debug=False)
