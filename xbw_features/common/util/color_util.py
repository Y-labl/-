# -*- coding: utf-8 -*-
# Assembled from decompiled bytecode of color_util.pyc

import random
import time
import cv2
from xbw_features.qtcompat import QPoint
from xbw_features.qtcompat import QColor
from loguru import logger
import numpy as np
from xbw_features.common.util.click_util import click
from xbw_features.common.util.math_util import isframeSame
from xbw_features.common.util.scrcpy_util import scrcpyUtil
from xbw_features import const

# module-level constants evaluated from bytecode

resultPopShowPointsAvoidChengJiu1 = [
 QPoint(165, 406),
 QPoint(200, 428)
]
resultPopShowPointsAvoidChengJiu2 = [
 QPoint(680, 406),
 QPoint(715, 428)
]
resultPopShowHasButtonPoints = [
 QPoint(595, 286),
 QPoint(600, 286),
 QPoint(605, 286),
 QPoint(610, 286),
 QPoint(615, 286),
 QPoint(620, 286)
]
hideEnterShowPoints = [
 QPoint(16, 163),
 QPoint(16, 164),
 QPoint(16, 165),
 QPoint(16, 166),
 QPoint(17, 162),
 QPoint(17, 163),
 QPoint(17, 164),
 QPoint(17, 165),
 QPoint(17, 166),
 QPoint(18, 164),
 QPoint(18, 165),
 QPoint(18, 166),
 QPoint(19, 164),
 QPoint(19, 165),
 QPoint(19, 166),
 QPoint(20, 163),
 QPoint(20, 164),
 QPoint(20, 166),
 QPoint(21, 152),
 QPoint(21, 162),
 QPoint(21, 166),
 QPoint(30, 163),
 QPoint(30, 166),
 QPoint(31, 163),
 QPoint(31, 164),
 QPoint(31, 165),
 QPoint(31, 166),
 QPoint(32, 152),
 QPoint(32, 164),
 QPoint(32, 165),
 QPoint(32, 166),
 QPoint(33, 163),
 QPoint(33, 164),
 QPoint(33, 165),
 QPoint(33, 166),
 QPoint(34, 163),
 QPoint(34, 164),
 QPoint(34, 165),
 QPoint(34, 166)
]
hidePlayerOpenPoints = [
 QPoint(11, 231),
 QPoint(11, 232),
 QPoint(18, 210),
 QPoint(19, 206),
 QPoint(19, 230),
 QPoint(20, 193),
 QPoint(20, 230),
 QPoint(21, 192),
 QPoint(22, 204),
 QPoint(23, 204),
 QPoint(24, 201),
 QPoint(24, 205),
 QPoint(24, 206),
 QPoint(25, 200),
 QPoint(25, 206),
 QPoint(25, 232),
 QPoint(26, 200),
 QPoint(31, 190),
 QPoint(33, 230),
 QPoint(34, 200),
 QPoint(35, 200),
 QPoint(35, 201),
 QPoint(36, 201),
 QPoint(37, 190),
 QPoint(39, 204),
 QPoint(40, 205),
 QPoint(40, 206),
 QPoint(40, 207),
 QPoint(41, 207),
 QPoint(46, 231),
 QPoint(48, 230),
 QPoint(52, 230)
]
hideTanweiOpenPoints = [
 QPoint(7, 293),
 QPoint(10, 293),
 QPoint(11, 293),
 QPoint(11, 294),
 QPoint(18, 257),
 QPoint(19, 256),
 QPoint(20, 255),
 QPoint(20, 270),
 QPoint(21, 254),
 QPoint(21, 264),
 QPoint(21, 270),
 QPoint(22, 266),
 QPoint(23, 252),
 QPoint(23, 267),
 QPoint(24, 267),
 QPoint(24, 268),
 QPoint(25, 268),
 QPoint(25, 269),
 QPoint(25, 294),
 QPoint(25, 295),
 QPoint(26, 264),
 QPoint(26, 269),
 QPoint(26, 270),
 QPoint(27, 264),
 QPoint(27, 265),
 QPoint(27, 271),
 QPoint(28, 262),
 QPoint(28, 264),
 QPoint(28, 265),
 QPoint(28, 266),
 QPoint(28, 267),
 QPoint(29, 262),
 QPoint(29, 264),
 QPoint(29, 265),
 QPoint(29, 266),
 QPoint(29, 267),
 QPoint(30, 262),
 QPoint(30, 264),
 QPoint(30, 265),
 QPoint(30, 266),
 QPoint(30, 267),
 QPoint(31, 252),
 QPoint(31, 262),
 QPoint(31, 264),
 QPoint(31, 265),
 QPoint(31, 266),
 QPoint(31, 267),
 QPoint(32, 262),
 QPoint(32, 264),
 QPoint(32, 265),
 QPoint(32, 266),
 QPoint(32, 267),
 QPoint(32, 294),
 QPoint(33, 264),
 QPoint(33, 265),
 QPoint(33, 266),
 QPoint(33, 267),
 QPoint(34, 263),
 QPoint(34, 264),
 QPoint(34, 265),
 QPoint(34, 266),
 QPoint(34, 267),
 QPoint(35, 263),
 QPoint(35, 264),
 QPoint(35, 265),
 QPoint(35, 266),
 QPoint(35, 267),
 QPoint(36, 252),
 QPoint(36, 264),
 QPoint(36, 265),
 QPoint(36, 266),
 QPoint(36, 267),
 QPoint(36, 268),
 QPoint(36, 269),
 QPoint(36, 270),
 QPoint(36, 271),
 QPoint(36, 272),
 QPoint(36, 273),
 QPoint(37, 264),
 QPoint(37, 265),
 QPoint(37, 267),
 QPoint(37, 268),
 QPoint(37, 269),
 QPoint(37, 270),
 QPoint(37, 271),
 QPoint(37, 272),
 QPoint(37, 273),
 QPoint(37, 294),
 QPoint(38, 266),
 QPoint(38, 268),
 QPoint(38, 269),
 QPoint(38, 294),
 QPoint(39, 266),
 QPoint(39, 267),
 QPoint(40, 256),
 QPoint(40, 268),
 QPoint(40, 269),
 QPoint(40, 270),
 QPoint(40, 271),
 QPoint(41, 269),
 QPoint(41, 270),
 QPoint(41, 271),
 QPoint(41, 272),
 QPoint(41, 273),
 QPoint(41, 294),
 QPoint(41, 295)
]
hideJiemianOpenPoints = [
 QPoint(9, 355),
 QPoint(10, 355),
 QPoint(11, 355),
 QPoint(12, 355),
 QPoint(13, 325),
 QPoint(15, 323),
 QPoint(16, 322),
 QPoint(19, 319),
 QPoint(20, 318),
 QPoint(21, 317),
 QPoint(21, 355),
 QPoint(21, 356),
 QPoint(21, 357),
 QPoint(22, 329),
 QPoint(22, 355),
 QPoint(22, 357),
 QPoint(23, 330),
 QPoint(23, 357),
 QPoint(24, 314),
 QPoint(24, 331),
 QPoint(25, 313),
 QPoint(25, 332),
 QPoint(25, 355),
 QPoint(25, 357),
 QPoint(26, 313),
 QPoint(26, 332),
 QPoint(26, 333),
 QPoint(26, 338),
 QPoint(26, 355),
 QPoint(26, 357),
 QPoint(27, 334),
 QPoint(27, 357),
 QPoint(28, 328),
 QPoint(28, 329),
 QPoint(28, 335),
 QPoint(28, 357),
 QPoint(29, 357),
 QPoint(30, 332),
 QPoint(30, 337),
 QPoint(31, 332),
 QPoint(31, 337),
 QPoint(32, 333),
 QPoint(32, 338),
 QPoint(33, 329),
 QPoint(33, 330),
 QPoint(33, 334),
 QPoint(34, 330),
 QPoint(35, 330),
 QPoint(35, 331),
 QPoint(36, 314),
 QPoint(36, 330),
 QPoint(36, 332),
 QPoint(36, 333),
 QPoint(37, 331),
 QPoint(37, 333),
 QPoint(37, 334),
 QPoint(37, 335),
 QPoint(37, 336),
 QPoint(37, 337),
 QPoint(37, 338),
 QPoint(38, 332),
 QPoint(38, 333),
 QPoint(39, 317),
 QPoint(39, 332),
 QPoint(39, 333),
 QPoint(39, 356),
 QPoint(39, 357),
 QPoint(40, 317),
 QPoint(41, 318),
 QPoint(41, 319),
 QPoint(45, 322),
 QPoint(48, 355),
 QPoint(49, 355),
 QPoint(50, 327),
 QPoint(50, 355),
 QPoint(51, 355),
 QPoint(51, 358),
 QPoint(52, 355),
 QPoint(53, 355),
 QPoint(53, 357),
 QPoint(54, 355),
 QPoint(55, 355),
 QPoint(56, 355),
 QPoint(56, 358),
 QPoint(57, 355)
]
OFFSET_0 = [
 QPoint(0, 0)
]
OFFSET_SEQUENCE0_1 = [
 QPoint(0, 0),
 QPoint(0, -1),
 QPoint(0, 1),
 QPoint(-1, 0),
 QPoint(1, 0),
 QPoint(-1, -1),
 QPoint(-1, 1),
 QPoint(1, -1),
 QPoint(1, 1)
]
OFFSET_SEQUENCE0_2 = [
 QPoint(0, 0),
 QPoint(0, -1),
 QPoint(0, 1),
 QPoint(-1, 0),
 QPoint(1, 0),
 QPoint(-1, -1),
 QPoint(-1, 1),
 QPoint(1, -1),
 QPoint(1, 1),
 QPoint(0, -2),
 QPoint(0, 2),
 QPoint(-2, 0),
 QPoint(2, 0),
 QPoint(-1, -2),
 QPoint(-1, 2),
 QPoint(1, -2),
 QPoint(1, 2),
 QPoint(-2, -1),
 QPoint(2, -1),
 QPoint(-2, 1),
 QPoint(2, 1),
 QPoint(-2, -2),
 QPoint(-2, 2),
 QPoint(2, -2),
 QPoint(2, 2)
]
typeNum1_0_Points = [
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(1, 0),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 8),
 QPoint(4, 1),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6)
]
typeNum1_1_Points = [
 QPoint(1, 1),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(2, 8)
]
typeNum1_2_Points = [
 QPoint(0, 1),
 QPoint(0, 8),
 QPoint(1, 0),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 6),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 5),
 QPoint(3, 8),
 QPoint(4, 0),
 QPoint(4, 4),
 QPoint(4, 8),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 8)
]
typeNum1_3_Points = [
 QPoint(0, 1),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(1, 0),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 4),
 QPoint(3, 0),
 QPoint(3, 4),
 QPoint(3, 8),
 QPoint(4, 0),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 8),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7)
]
typeNum1_4_Points = [
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(1, 4),
 QPoint(1, 6),
 QPoint(2, 3),
 QPoint(2, 6),
 QPoint(3, 1),
 QPoint(3, 2),
 QPoint(3, 6),
 QPoint(4, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8)
]
typeNum1_5_Points = [
 QPoint(0, 1),
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 7),
 QPoint(1, 0),
 QPoint(1, 3),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 3),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 3),
 QPoint(3, 8),
 QPoint(4, 0),
 QPoint(4, 4),
 QPoint(4, 8),
 QPoint(5, 6)
]
typeNum1_6_Points = [
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(1, 0),
 QPoint(1, 4),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 3),
 QPoint(3, 0),
 QPoint(3, 3),
 QPoint(3, 8),
 QPoint(4, 0),
 QPoint(4, 4),
 QPoint(4, 8),
 QPoint(5, 5),
 QPoint(5, 6)
]
typeNum1_7_Points = [
 QPoint(0, 0),
 QPoint(1, 0),
 QPoint(2, 0),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 2),
 QPoint(3, 3),
 QPoint(4, 0),
 QPoint(4, 1)
]
typeNum1_8_Points = [
 QPoint(0, 1),
 QPoint(0, 2),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(1, 0),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 4),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 4),
 QPoint(3, 8),
 QPoint(4, 1),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 8),
 QPoint(5, 2),
 QPoint(5, 6),
 QPoint(5, 7)
]
typeNum1_9_Points = [
 QPoint(0, 1),
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 7),
 QPoint(1, 0),
 QPoint(1, 5),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 5),
 QPoint(3, 0),
 QPoint(3, 5),
 QPoint(3, 8),
 QPoint(4, 1),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6)
]
type1NumPointsList = [
 [
  QPoint(0, 5),
  QPoint(0, 6),
  QPoint(1, 4),
  QPoint(1, 6),
  QPoint(2, 3),
  QPoint(2, 6),
  QPoint(3, 1),
  QPoint(3, 2),
  QPoint(3, 6),
  QPoint(4, 0),
  QPoint(4, 1),
  QPoint(4, 2),
  QPoint(4, 3),
  QPoint(4, 4),
  QPoint(4, 5),
  QPoint(4, 6),
  QPoint(4, 7),
  QPoint(4, 8)
 ],
 [
  QPoint(0, 1),
  QPoint(0, 8),
  QPoint(1, 0),
  QPoint(1, 6),
  QPoint(1, 7),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 6),
  QPoint(2, 8),
  QPoint(3, 0),
  QPoint(3, 5),
  QPoint(3, 8),
  QPoint(4, 0),
  QPoint(4, 4),
  QPoint(4, 8),
  QPoint(5, 1),
  QPoint(5, 2),
  QPoint(5, 8)
 ],
 [
  QPoint(0, 1),
  QPoint(0, 2),
  QPoint(0, 5),
  QPoint(0, 6),
  QPoint(0, 7),
  QPoint(0, 8),
  QPoint(1, 0),
  QPoint(1, 3),
  QPoint(1, 4),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 4),
  QPoint(2, 8),
  QPoint(3, 0),
  QPoint(3, 4),
  QPoint(3, 8),
  QPoint(4, 1),
  QPoint(4, 3),
  QPoint(4, 4),
  QPoint(4, 8),
  QPoint(5, 2),
  QPoint(5, 6),
  QPoint(5, 7)
 ],
 [
  QPoint(0, 1),
  QPoint(0, 2),
  QPoint(0, 3),
  QPoint(0, 4),
  QPoint(0, 7),
  QPoint(1, 0),
  QPoint(1, 5),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 5),
  QPoint(3, 0),
  QPoint(3, 5),
  QPoint(3, 8),
  QPoint(4, 1),
  QPoint(4, 4),
  QPoint(4, 5),
  QPoint(4, 7),
  QPoint(4, 8),
  QPoint(5, 3),
  QPoint(5, 4),
  QPoint(5, 5),
  QPoint(5, 6)
 ],
 [
  QPoint(0, 1),
  QPoint(0, 7),
  QPoint(0, 8),
  QPoint(1, 0),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 4),
  QPoint(3, 0),
  QPoint(3, 4),
  QPoint(3, 8),
  QPoint(4, 0),
  QPoint(4, 3),
  QPoint(4, 4),
  QPoint(4, 5),
  QPoint(4, 8),
  QPoint(5, 1),
  QPoint(5, 2),
  QPoint(5, 5),
  QPoint(5, 6),
  QPoint(5, 7)
 ],
 [
  QPoint(0, 2),
  QPoint(0, 3),
  QPoint(0, 4),
  QPoint(0, 5),
  QPoint(0, 6),
  QPoint(1, 0),
  QPoint(1, 4),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 3),
  QPoint(3, 0),
  QPoint(3, 3),
  QPoint(3, 8),
  QPoint(4, 0),
  QPoint(4, 4),
  QPoint(4, 8),
  QPoint(5, 5),
  QPoint(5, 6)
 ],
 [
  QPoint(0, 1),
  QPoint(0, 2),
  QPoint(0, 3),
  QPoint(0, 4),
  QPoint(0, 7),
  QPoint(1, 0),
  QPoint(1, 3),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 3),
  QPoint(2, 8),
  QPoint(3, 0),
  QPoint(3, 3),
  QPoint(3, 8),
  QPoint(4, 0),
  QPoint(4, 4),
  QPoint(4, 8),
  QPoint(5, 6)
 ],
 [
  QPoint(0, 0),
  QPoint(1, 0),
  QPoint(2, 0),
  QPoint(2, 4),
  QPoint(2, 5),
  QPoint(2, 6),
  QPoint(2, 7),
  QPoint(2, 8),
  QPoint(3, 0),
  QPoint(3, 2),
  QPoint(3, 3),
  QPoint(4, 0),
  QPoint(4, 1)
 ],
 [
  QPoint(0, 2),
  QPoint(0, 3),
  QPoint(0, 4),
  QPoint(0, 5),
  QPoint(0, 6),
  QPoint(0, 7),
  QPoint(1, 0),
  QPoint(1, 8),
  QPoint(2, 0),
  QPoint(2, 8),
  QPoint(3, 0),
  QPoint(3, 8),
  QPoint(4, 1),
  QPoint(4, 7),
  QPoint(4, 8),
  QPoint(5, 2),
  QPoint(5, 3),
  QPoint(5, 4),
  QPoint(5, 5),
  QPoint(5, 6)
 ],
 [
  QPoint(1, 1),
  QPoint(2, 0),
  QPoint(2, 1),
  QPoint(2, 2),
  QPoint(2, 3),
  QPoint(2, 4),
  QPoint(2, 5),
  QPoint(2, 6),
  QPoint(2, 7),
  QPoint(2, 8)
 ]
]
numResList = [
 4,
 2,
 8,
 9,
 3,
 6,
 5,
 7,
 0,
 1
]
PKG_CENTER_GVN_NPC = QPoint(285, 129)
PKG_CENTER_CUR_PKG = QPoint(400, 135)
ziDongTextPoints = [
 QPoint(351, 308),
 QPoint(351, 310),
 QPoint(351, 311),
 QPoint(351, 313),
 QPoint(351, 314),
 QPoint(352, 317),
 QPoint(353, 307),
 QPoint(353, 317),
 QPoint(354, 307),
 QPoint(355, 307),
 QPoint(356, 307),
 QPoint(357, 307),
 QPoint(359, 317),
 QPoint(360, 308),
 QPoint(360, 310),
 QPoint(360, 311),
 QPoint(360, 313),
 QPoint(360, 314),
 QPoint(364, 311),
 QPoint(364, 314),
 QPoint(364, 316),
 QPoint(365, 311),
 QPoint(366, 311),
 QPoint(367, 315),
 QPoint(368, 316),
 QPoint(369, 309),
 QPoint(369, 316),
 QPoint(370, 309),
 QPoint(370, 313),
 QPoint(371, 308),
 QPoint(371, 309),
 QPoint(372, 309),
 QPoint(372, 317),
 QPoint(373, 309),
 QPoint(373, 317),
 QPoint(374, 310),
 QPoint(374, 311),
 QPoint(374, 312),
 QPoint(374, 313),
 QPoint(374, 314),
 QPoint(374, 315)
]
JumpGray_ShangHui_OneDianPu = QPoint(182, 390)
JumpGray_ShangHui_AllDianPu = QPoint(245, 394)
JumpGray_Resp = QPoint(0, 0)
zaiTextPoints = [
 QPoint(0, 0),
 QPoint(1, 0),
 QPoint(2, 0),
 QPoint(3, 0),
 QPoint(4, 0),
 QPoint(5, 0),
 QPoint(6, 0),
 QPoint(7, 0),
 QPoint(8, 0),
 QPoint(9, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(1, 3),
 QPoint(0, 4),
 QPoint(1, 4),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(2, 8),
 QPoint(3, 8),
 QPoint(4, 8),
 QPoint(5, 8),
 QPoint(6, 8),
 QPoint(7, 8),
 QPoint(8, 8),
 QPoint(9, 8),
 QPoint(4, 4),
 QPoint(5, 4),
 QPoint(6, 4),
 QPoint(6, 3),
 QPoint(7, 4)
]
zaiTextPoints_Bg = [
 QPoint(0, 2),
 QPoint(4, 2),
 QPoint(7, 2),
 QPoint(8, 2),
 QPoint(9, 2),
 QPoint(2, 6),
 QPoint(3, 6),
 QPoint(4, 6),
 QPoint(3, 7),
 QPoint(4, 7),
 QPoint(7, 6),
 QPoint(8, 6),
 QPoint(9, 6),
 QPoint(7, 2),
 QPoint(8, 2),
 QPoint(9, 2)
]
qingTextPoints = [
 QPoint(0, 0),
 QPoint(1, 0),
 QPoint(2, 0),
 QPoint(3, 0),
 QPoint(4, 0),
 QPoint(5, 0),
 QPoint(2, 1),
 QPoint(3, 1),
 QPoint(1, 2),
 QPoint(2, 2),
 QPoint(3, 2),
 QPoint(4, 2),
 QPoint(1, 3),
 QPoint(2, 3),
 QPoint(3, 3),
 QPoint(4, 3),
 QPoint(1, 4),
 QPoint(2, 4),
 QPoint(3, 4),
 QPoint(4, 4),
 QPoint(0, 5),
 QPoint(1, 5),
 QPoint(2, 5),
 QPoint(3, 5),
 QPoint(4, 5),
 QPoint(5, 5),
 QPoint(0, 6),
 QPoint(1, 6),
 QPoint(2, 6),
 QPoint(3, 6),
 QPoint(4, 6),
 QPoint(5, 6),
 QPoint(0, 7),
 QPoint(5, 7),
 QPoint(0, 8),
 QPoint(5, 5),
 QPoint(0, 9),
 QPoint(4, 9),
 QPoint(5, 9)
]
baobaoRedPoints = [
 QPoint(1, 0),
 QPoint(2, 0),
 QPoint(3, 0),
 QPoint(4, 0),
 QPoint(5, 0),
 QPoint(6, 0),
 QPoint(7, 0),
 QPoint(8, 0),
 QPoint(9, 0),
 QPoint(10, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7),
 QPoint(5, 8),
 QPoint(6, 4),
 QPoint(7, 4),
 QPoint(6, 8),
 QPoint(7, 8),
 QPoint(8, 8),
 QPoint(16, 0),
 QPoint(17, 0),
 QPoint(18, 0),
 QPoint(19, 0),
 QPoint(20, 0),
 QPoint(21, 0),
 QPoint(22, 0),
 QPoint(23, 0),
 QPoint(24, 0),
 QPoint(25, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 8),
 QPoint(21, 4),
 QPoint(22, 4),
 QPoint(21, 8),
 QPoint(22, 8),
 QPoint(23, 8)
]
baobaoRedPoints_Bg = [
 QPoint(1, 2),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(10, 2),
 QPoint(10, 3),
 QPoint(10, 4),
 QPoint(10, 5),
 QPoint(10, 6),
 QPoint(15, 2),
 QPoint(16, 2),
 QPoint(15, 5),
 QPoint(16, 5),
 QPoint(17, 5),
 QPoint(15, 6),
 QPoint(16, 6),
 QPoint(17, 6),
 QPoint(15, 7),
 QPoint(16, 7),
 QPoint(17, 7),
 QPoint(26, 1),
 QPoint(26, 2),
 QPoint(26, 3),
 QPoint(26, 4),
 QPoint(26, 5),
 QPoint(26, 6),
 QPoint(26, 7)
]
baobaoBluePoints = [
 QPoint(0, 0),
 QPoint(1, 0),
 QPoint(2, 0),
 QPoint(3, 0),
 QPoint(4, 0),
 QPoint(5, 0),
 QPoint(6, 0),
 QPoint(7, 0),
 QPoint(8, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(3, 4),
 QPoint(5, 4),
 QPoint(6, 4),
 QPoint(3, 8),
 QPoint(5, 8),
 QPoint(6, 8),
 QPoint(7, 8),
 QPoint(16, 0),
 QPoint(17, 0),
 QPoint(18, 0),
 QPoint(19, 0),
 QPoint(20, 0),
 QPoint(21, 0),
 QPoint(22, 0),
 QPoint(19, 1),
 QPoint(19, 2),
 QPoint(19, 3),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 7),
 QPoint(19, 8),
 QPoint(18, 4),
 QPoint(20, 4),
 QPoint(18, 8),
 QPoint(20, 8),
 QPoint(21, 8),
 QPoint(22, 8),
 QPoint(23, 8)
]
baobaoBluePoints_Bg = [
 QPoint(0, 2),
 QPoint(1, 2),
 QPoint(2, 2),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(6, 2),
 QPoint(7, 2),
 QPoint(8, 2),
 QPoint(14, 2),
 QPoint(15, 2),
 QPoint(16, 2),
 QPoint(17, 2),
 QPoint(21, 2),
 QPoint(22, 2),
 QPoint(23, 2),
 QPoint(14, 5),
 QPoint(15, 5),
 QPoint(16, 5),
 QPoint(14, 6),
 QPoint(15, 6),
 QPoint(16, 6),
 QPoint(14, 7),
 QPoint(15, 7),
 QPoint(16, 7)
]
wenYiRedPoints = [
 QPoint(0, 1),
 QPoint(1, 1),
 QPoint(2, 4),
 QPoint(2, 7),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(5, 0),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(6, 4),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(7, 4),
 QPoint(7, 6),
 QPoint(7, 7),
 QPoint(8, 7),
 QPoint(9, 8),
 QPoint(14, 0),
 QPoint(16, 1),
 QPoint(16, 4),
 QPoint(16, 7),
 QPoint(16, 8),
 QPoint(16, 9),
 QPoint(17, 4),
 QPoint(17, 6),
 QPoint(17, 7),
 QPoint(17, 8),
 QPoint(17, 9),
 QPoint(18, 0),
 QPoint(18, 4),
 QPoint(18, 5),
 QPoint(18, 6),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 9),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 8),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 6),
 QPoint(21, 7),
 QPoint(21, 8),
 QPoint(22, 0),
 QPoint(22, 1),
 QPoint(22, 2),
 QPoint(22, 3),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 7),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 2),
 QPoint(23, 3),
 QPoint(23, 8),
 QPoint(24, 0),
 QPoint(24, 1),
 QPoint(24, 2),
 QPoint(24, 3),
 QPoint(24, 8),
 QPoint(25, 0),
 QPoint(25, 1),
 QPoint(25, 2),
 QPoint(25, 3),
 QPoint(25, 4),
 QPoint(25, 5),
 QPoint(25, 6),
 QPoint(25, 7),
 QPoint(25, 8),
 QPoint(25, 9)
]
chaoLiangBaoJiRedPoints = [
 QPoint(0, 0),
 QPoint(0, 1),
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(1, 0),
 QPoint(1, 1),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 8),
 QPoint(3, 0),
 QPoint(3, 1),
 QPoint(3, 2),
 QPoint(3, 3),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(3, 8),
 QPoint(4, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 6),
 QPoint(4, 8),
 QPoint(5, 0),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 6),
 QPoint(5, 8),
 QPoint(6, 1),
 QPoint(6, 2),
 QPoint(6, 3),
 QPoint(6, 8),
 QPoint(6, 9),
 QPoint(7, 1),
 QPoint(7, 2),
 QPoint(7, 3),
 QPoint(7, 8),
 QPoint(7, 9),
 QPoint(8, 0),
 QPoint(8, 1),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 4),
 QPoint(8, 5),
 QPoint(8, 6),
 QPoint(8, 7),
 QPoint(8, 8),
 QPoint(8, 9),
 QPoint(9, 0),
 QPoint(9, 2),
 QPoint(9, 3),
 QPoint(9, 4),
 QPoint(9, 5),
 QPoint(9, 6),
 QPoint(9, 7),
 QPoint(9, 8),
 QPoint(9, 9),
 QPoint(14, 0),
 QPoint(14, 1),
 QPoint(14, 2),
 QPoint(14, 3),
 QPoint(14, 4),
 QPoint(14, 5),
 QPoint(14, 6),
 QPoint(14, 7),
 QPoint(14, 8),
 QPoint(14, 9),
 QPoint(15, 0),
 QPoint(15, 1),
 QPoint(15, 2),
 QPoint(15, 3),
 QPoint(15, 4),
 QPoint(15, 5),
 QPoint(15, 6),
 QPoint(15, 7),
 QPoint(15, 8),
 QPoint(15, 9),
 QPoint(16, 0),
 QPoint(16, 1),
 QPoint(16, 2),
 QPoint(16, 3),
 QPoint(16, 4),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(16, 7),
 QPoint(16, 8),
 QPoint(16, 9),
 QPoint(17, 0),
 QPoint(17, 1),
 QPoint(17, 2),
 QPoint(17, 3),
 QPoint(17, 4),
 QPoint(17, 5),
 QPoint(17, 6),
 QPoint(17, 7),
 QPoint(17, 8),
 QPoint(17, 9),
 QPoint(18, 0),
 QPoint(18, 1),
 QPoint(18, 2),
 QPoint(18, 3),
 QPoint(18, 4),
 QPoint(18, 5),
 QPoint(18, 6),
 QPoint(18, 7),
 QPoint(18, 8),
 QPoint(18, 9),
 QPoint(19, 0),
 QPoint(19, 1),
 QPoint(19, 2),
 QPoint(19, 3),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 7),
 QPoint(19, 8),
 QPoint(19, 9),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 8),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 1),
 QPoint(21, 2),
 QPoint(21, 3),
 QPoint(21, 4),
 QPoint(21, 5),
 QPoint(21, 6),
 QPoint(21, 7),
 QPoint(21, 8),
 QPoint(21, 9),
 QPoint(22, 0),
 QPoint(22, 1),
 QPoint(22, 2),
 QPoint(22, 3),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 7),
 QPoint(22, 8),
 QPoint(22, 9),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 2),
 QPoint(23, 3),
 QPoint(23, 4),
 QPoint(23, 5),
 QPoint(23, 6),
 QPoint(23, 7),
 QPoint(23, 8),
 QPoint(23, 9),
 QPoint(24, 8),
 QPoint(24, 9),
 QPoint(28, 0),
 QPoint(28, 1),
 QPoint(28, 2),
 QPoint(28, 3),
 QPoint(28, 4),
 QPoint(28, 5),
 QPoint(29, 0),
 QPoint(29, 1),
 QPoint(29, 2),
 QPoint(29, 3),
 QPoint(29, 4),
 QPoint(29, 5),
 QPoint(30, 0),
 QPoint(30, 1),
 QPoint(30, 2),
 QPoint(30, 3),
 QPoint(30, 4),
 QPoint(30, 5),
 QPoint(30, 6),
 QPoint(30, 7),
 QPoint(31, 0),
 QPoint(31, 1),
 QPoint(31, 2),
 QPoint(31, 3),
 QPoint(31, 4),
 QPoint(31, 5),
 QPoint(31, 6),
 QPoint(31, 7),
 QPoint(31, 8),
 QPoint(31, 9),
 QPoint(32, 0),
 QPoint(32, 1),
 QPoint(32, 2),
 QPoint(32, 3),
 QPoint(32, 4),
 QPoint(32, 5),
 QPoint(32, 6),
 QPoint(32, 7),
 QPoint(32, 8),
 QPoint(32, 9),
 QPoint(33, 0),
 QPoint(33, 1),
 QPoint(33, 2),
 QPoint(33, 3),
 QPoint(33, 4),
 QPoint(33, 5),
 QPoint(33, 6),
 QPoint(33, 7),
 QPoint(33, 8),
 QPoint(34, 0),
 QPoint(34, 1),
 QPoint(34, 2),
 QPoint(34, 3),
 QPoint(34, 4),
 QPoint(34, 5),
 QPoint(34, 6),
 QPoint(34, 7),
 QPoint(35, 0),
 QPoint(35, 1),
 QPoint(35, 2),
 QPoint(35, 3),
 QPoint(35, 4),
 QPoint(35, 5),
 QPoint(35, 6),
 QPoint(35, 7),
 QPoint(36, 0),
 QPoint(36, 1),
 QPoint(36, 2),
 QPoint(36, 3),
 QPoint(36, 4),
 QPoint(36, 5),
 QPoint(36, 6),
 QPoint(36, 7),
 QPoint(37, 0),
 QPoint(37, 1),
 QPoint(37, 2),
 QPoint(37, 3),
 QPoint(37, 4),
 QPoint(37, 5),
 QPoint(37, 7),
 QPoint(38, 0),
 QPoint(38, 1),
 QPoint(38, 2),
 QPoint(38, 3),
 QPoint(38, 4),
 QPoint(38, 5),
 QPoint(38, 6),
 QPoint(38, 7),
 QPoint(38, 8),
 QPoint(39, 0),
 QPoint(39, 1),
 QPoint(39, 2),
 QPoint(39, 3),
 QPoint(39, 4),
 QPoint(39, 5),
 QPoint(39, 6),
 QPoint(48, 0),
 QPoint(48, 1),
 QPoint(48, 2),
 QPoint(48, 3),
 QPoint(48, 4),
 QPoint(48, 5),
 QPoint(48, 6),
 QPoint(48, 8),
 QPoint(49, 0),
 QPoint(49, 1),
 QPoint(49, 2),
 QPoint(49, 3),
 QPoint(49, 8),
 QPoint(50, 1),
 QPoint(50, 2),
 QPoint(50, 8),
 QPoint(51, 1),
 QPoint(51, 2),
 QPoint(51, 8),
 QPoint(52, 8),
 QPoint(53, 8)
]
jingyingRedPoints = [
 QPoint(0, 0),
 QPoint(0, 1),
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(1, 0),
 QPoint(1, 1),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(2, 9),
 QPoint(3, 0),
 QPoint(3, 1),
 QPoint(3, 2),
 QPoint(3, 3),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(3, 7),
 QPoint(3, 9),
 QPoint(4, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(4, 9),
 QPoint(5, 0),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7),
 QPoint(5, 8),
 QPoint(5, 9),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(8, 5),
 QPoint(9, 4),
 QPoint(10, 0),
 QPoint(10, 1),
 QPoint(10, 2),
 QPoint(10, 4),
 QPoint(10, 5),
 QPoint(10, 6),
 QPoint(10, 8),
 QPoint(10, 9),
 QPoint(11, 0),
 QPoint(11, 1),
 QPoint(11, 5),
 QPoint(11, 6),
 QPoint(11, 8),
 QPoint(12, 0),
 QPoint(12, 1),
 QPoint(12, 5),
 QPoint(12, 6),
 QPoint(12, 7),
 QPoint(12, 8),
 QPoint(13, 0),
 QPoint(13, 1),
 QPoint(13, 5),
 QPoint(13, 6),
 QPoint(13, 7),
 QPoint(14, 0),
 QPoint(14, 1),
 QPoint(14, 2),
 QPoint(14, 3),
 QPoint(14, 4),
 QPoint(14, 5),
 QPoint(14, 6),
 QPoint(14, 7),
 QPoint(15, 0),
 QPoint(15, 1),
 QPoint(15, 2),
 QPoint(15, 3),
 QPoint(15, 4),
 QPoint(15, 5),
 QPoint(15, 6),
 QPoint(15, 7),
 QPoint(16, 0),
 QPoint(16, 1),
 QPoint(16, 2),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(16, 7),
 QPoint(17, 0),
 QPoint(17, 1),
 QPoint(17, 2),
 QPoint(17, 5),
 QPoint(17, 6),
 QPoint(17, 7),
 QPoint(17, 8),
 QPoint(18, 0),
 QPoint(18, 1),
 QPoint(18, 5),
 QPoint(18, 6),
 QPoint(18, 7),
 QPoint(18, 8),
 QPoint(18, 9),
 QPoint(19, 0),
 QPoint(19, 1),
 QPoint(19, 2),
 QPoint(19, 3),
 QPoint(19, 4),
 QPoint(19, 6),
 QPoint(19, 8),
 QPoint(19, 9),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 9),
 QPoint(21, 5)
]
jingyingRedPoints_Bg = [
 QPoint(8, 0),
 QPoint(9, 0),
 QPoint(8, 1),
 QPoint(9, 1),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 7),
 QPoint(9, 7),
 QPoint(11, 3),
 QPoint(14, 8),
 QPoint(18, 3),
 QPoint(20, 0),
 QPoint(21, 0),
 QPoint(20, 2),
 QPoint(21, 2),
 QPoint(21, 3),
 QPoint(20, 7)
]
huyouRedPoints = [
 QPoint(0, 2),
 QPoint(0, 6),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(1, 9),
 QPoint(2, 2),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 7),
 QPoint(3, 9),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(6, 0),
 QPoint(6, 4),
 QPoint(6, 5),
 QPoint(7, 0),
 QPoint(7, 4),
 QPoint(7, 5),
 QPoint(8, 0),
 QPoint(8, 1),
 QPoint(9, 0),
 QPoint(9, 1),
 QPoint(10, 0),
 QPoint(10, 3),
 QPoint(10, 4),
 QPoint(11, 0),
 QPoint(11, 1),
 QPoint(11, 2),
 QPoint(11, 3),
 QPoint(11, 4),
 QPoint(14, 4),
 QPoint(14, 5),
 QPoint(15, 4),
 QPoint(15, 5),
 QPoint(15, 6),
 QPoint(15, 7),
 QPoint(16, 4),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(16, 7),
 QPoint(17, 6),
 QPoint(17, 7),
 QPoint(18, 0),
 QPoint(18, 1),
 QPoint(18, 6),
 QPoint(18, 9),
 QPoint(19, 0),
 QPoint(19, 1),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 7),
 QPoint(19, 8),
 QPoint(19, 9),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 1),
 QPoint(21, 2),
 QPoint(21, 4),
 QPoint(21, 5),
 QPoint(22, 0),
 QPoint(22, 1),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 4),
 QPoint(23, 5),
 QPoint(26, 6),
 QPoint(26, 7)
]
huyouRedPoints_Bg = [
 QPoint(6, 8),
 QPoint(7, 8),
 QPoint(8, 8),
 QPoint(9, 8),
 QPoint(10, 8),
 QPoint(11, 8),
 QPoint(12, 8),
 QPoint(13, 8),
 QPoint(6, 9),
 QPoint(7, 9),
 QPoint(8, 9),
 QPoint(9, 9),
 QPoint(10, 9),
 QPoint(11, 9),
 QPoint(12, 9),
 QPoint(13, 9),
 QPoint(6, 10),
 QPoint(7, 10),
 QPoint(8, 10),
 QPoint(9, 10),
 QPoint(10, 10),
 QPoint(11, 10),
 QPoint(12, 10),
 QPoint(13, 10),
 QPoint(6, 11),
 QPoint(7, 11),
 QPoint(8, 11),
 QPoint(9, 11),
 QPoint(10, 11),
 QPoint(11, 11),
 QPoint(12, 11),
 QPoint(13, 11),
 QPoint(6, 12),
 QPoint(7, 12),
 QPoint(8, 12),
 QPoint(9, 12),
 QPoint(10, 12),
 QPoint(11, 12),
 QPoint(12, 12),
 QPoint(13, 12),
 QPoint(22, 6),
 QPoint(23, 6),
 QPoint(22, 7),
 QPoint(23, 7),
 QPoint(22, 8),
 QPoint(23, 8),
 QPoint(22, 9),
 QPoint(23, 9)
]
baozhaRedPoints = [
 QPoint(0, 0),
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(1, 1),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 8),
 QPoint(1, 9),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(2, 8),
 QPoint(2, 9),
 QPoint(3, 0),
 QPoint(3, 1),
 QPoint(3, 2),
 QPoint(3, 3),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(3, 7),
 QPoint(3, 9),
 QPoint(4, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(4, 9),
 QPoint(5, 0),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7),
 QPoint(5, 8),
 QPoint(5, 9),
 QPoint(6, 0),
 QPoint(6, 1),
 QPoint(6, 2),
 QPoint(6, 3),
 QPoint(6, 4),
 QPoint(6, 5),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(6, 8),
 QPoint(6, 9),
 QPoint(7, 0),
 QPoint(7, 1),
 QPoint(7, 2),
 QPoint(7, 3),
 QPoint(7, 4),
 QPoint(7, 5),
 QPoint(7, 6),
 QPoint(7, 7),
 QPoint(7, 8),
 QPoint(7, 9),
 QPoint(8, 0),
 QPoint(8, 1),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 4),
 QPoint(8, 5),
 QPoint(8, 6),
 QPoint(8, 7),
 QPoint(8, 8),
 QPoint(8, 9),
 QPoint(9, 0),
 QPoint(9, 1),
 QPoint(9, 2),
 QPoint(9, 3),
 QPoint(9, 4),
 QPoint(9, 5),
 QPoint(9, 6),
 QPoint(9, 7),
 QPoint(9, 8),
 QPoint(9, 9),
 QPoint(10, 0),
 QPoint(10, 1),
 QPoint(10, 2),
 QPoint(10, 3),
 QPoint(10, 4),
 QPoint(10, 5),
 QPoint(10, 6),
 QPoint(10, 7),
 QPoint(10, 8),
 QPoint(10, 9),
 QPoint(11, 0),
 QPoint(11, 2),
 QPoint(11, 3),
 QPoint(11, 4),
 QPoint(11, 5),
 QPoint(11, 6),
 QPoint(11, 7),
 QPoint(11, 8),
 QPoint(14, 3),
 QPoint(15, 2),
 QPoint(15, 3),
 QPoint(15, 4),
 QPoint(15, 5),
 QPoint(16, 0),
 QPoint(16, 1),
 QPoint(16, 2),
 QPoint(16, 3),
 QPoint(16, 4),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(16, 7),
 QPoint(16, 8),
 QPoint(17, 1),
 QPoint(17, 2),
 QPoint(17, 3),
 QPoint(17, 8),
 QPoint(17, 9),
 QPoint(18, 0),
 QPoint(18, 1),
 QPoint(18, 2),
 QPoint(18, 3),
 QPoint(19, 0),
 QPoint(19, 1),
 QPoint(19, 2),
 QPoint(19, 3),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(21, 0),
 QPoint(21, 1),
 QPoint(21, 2),
 QPoint(21, 3),
 QPoint(22, 0),
 QPoint(22, 1),
 QPoint(22, 2),
 QPoint(22, 3),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 8),
 QPoint(22, 9),
 QPoint(23, 0),
 QPoint(23, 3),
 QPoint(23, 7),
 QPoint(23, 8),
 QPoint(24, 0),
 QPoint(24, 3),
 QPoint(24, 7),
 QPoint(25, 0),
 QPoint(25, 3),
 QPoint(25, 7)
]
baozhaRedPoints_Bg = [
 QPoint(19, 4),
 QPoint(20, 4),
 QPoint(18, 5),
 QPoint(19, 5),
 QPoint(20, 5),
 QPoint(18, 6),
 QPoint(19, 6),
 QPoint(20, 6),
 QPoint(21, 6),
 QPoint(18, 7),
 QPoint(19, 7),
 QPoint(20, 7),
 QPoint(21, 7),
 QPoint(18, 8),
 QPoint(19, 8),
 QPoint(20, 8),
 QPoint(21, 8),
 QPoint(18, 9),
 QPoint(19, 9),
 QPoint(20, 9),
 QPoint(21, 9),
 QPoint(18, 10),
 QPoint(19, 10),
 QPoint(20, 10),
 QPoint(21, 10),
 QPoint(18, 11),
 QPoint(19, 11),
 QPoint(20, 11),
 QPoint(21, 11),
 QPoint(15, 10),
 QPoint(16, 10),
 QPoint(15, 11),
 QPoint(16, 11),
 QPoint(24, 1),
 QPoint(25, 1),
 QPoint(24, 5),
 QPoint(25, 5),
 QPoint(25, 9),
 QPoint(23, 10),
 QPoint(24, 10),
 QPoint(25, 10),
 QPoint(23, 11),
 QPoint(24, 11),
 QPoint(25, 11)
]
toulingRedPoints = [
 QPoint(0, 1),
 QPoint(1, 1),
 QPoint(2, 4),
 QPoint(2, 7),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(4, 4),
 QPoint(4, 5),
 QPoint(4, 6),
 QPoint(5, 0),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(6, 4),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(7, 4),
 QPoint(7, 6),
 QPoint(7, 7),
 QPoint(8, 7),
 QPoint(9, 8),
 QPoint(14, 0),
 QPoint(16, 1),
 QPoint(16, 4),
 QPoint(16, 7),
 QPoint(16, 8),
 QPoint(16, 9),
 QPoint(17, 4),
 QPoint(17, 6),
 QPoint(17, 7),
 QPoint(17, 8),
 QPoint(17, 9),
 QPoint(18, 0),
 QPoint(18, 4),
 QPoint(18, 5),
 QPoint(18, 6),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 9),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 8),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 6),
 QPoint(21, 7),
 QPoint(21, 8),
 QPoint(22, 0),
 QPoint(22, 1),
 QPoint(22, 2),
 QPoint(22, 3),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 7),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 2),
 QPoint(23, 3),
 QPoint(23, 8),
 QPoint(24, 0),
 QPoint(24, 1),
 QPoint(24, 2),
 QPoint(24, 3),
 QPoint(24, 8),
 QPoint(25, 0),
 QPoint(25, 1),
 QPoint(25, 2),
 QPoint(25, 3),
 QPoint(25, 4),
 QPoint(25, 5),
 QPoint(25, 6),
 QPoint(25, 7),
 QPoint(25, 8),
 QPoint(25, 9)
]
toulingRedPoints_Bg = [
 QPoint(2, 1),
 QPoint(3, 1),
 QPoint(2, 2),
 QPoint(3, 2),
 QPoint(2, 3),
 QPoint(3, 3),
 QPoint(6, 0),
 QPoint(7, 0),
 QPoint(8, 0),
 QPoint(9, 0),
 QPoint(10, 0),
 QPoint(11, 0),
 QPoint(12, 0),
 QPoint(6, 1),
 QPoint(7, 1),
 QPoint(8, 1),
 QPoint(9, 1),
 QPoint(10, 1),
 QPoint(11, 1),
 QPoint(12, 1),
 QPoint(6, 2),
 QPoint(7, 2),
 QPoint(8, 2),
 QPoint(9, 2),
 QPoint(10, 2),
 QPoint(11, 2),
 QPoint(12, 2),
 QPoint(8, 3),
 QPoint(9, 3),
 QPoint(10, 3),
 QPoint(11, 3),
 QPoint(12, 3),
 QPoint(0, 6),
 QPoint(1, 6),
 QPoint(4, 8),
 QPoint(5, 8),
 QPoint(6, 8),
 QPoint(7, 8),
 QPoint(3, 9),
 QPoint(4, 9),
 QPoint(5, 9),
 QPoint(6, 9),
 QPoint(7, 9),
 QPoint(8, 5),
 QPoint(9, 5),
 QPoint(10, 5),
 QPoint(11, 5),
 QPoint(12, 5),
 QPoint(13, 5),
 QPoint(16, 5),
 QPoint(10, 6),
 QPoint(11, 6),
 QPoint(10, 7),
 QPoint(11, 7),
 QPoint(15, 5),
 QPoint(15, 9),
 QPoint(18, 2)
]
jinshenRedPoints = [
 QPoint(0, 0),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 9),
 QPoint(3, 0),
 QPoint(3, 1),
 QPoint(3, 3),
 QPoint(3, 9),
 QPoint(4, 0),
 QPoint(4, 1),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(5, 0),
 QPoint(5, 1),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 5),
 QPoint(5, 9),
 QPoint(6, 0),
 QPoint(6, 2),
 QPoint(6, 3),
 QPoint(6, 8),
 QPoint(6, 9),
 QPoint(7, 0),
 QPoint(7, 1),
 QPoint(7, 2),
 QPoint(7, 3),
 QPoint(7, 5),
 QPoint(7, 9),
 QPoint(8, 0),
 QPoint(8, 1),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 8),
 QPoint(9, 0),
 QPoint(9, 2),
 QPoint(9, 3),
 QPoint(9, 8),
 QPoint(10, 0),
 QPoint(10, 1),
 QPoint(11, 0),
 QPoint(16, 0),
 QPoint(16, 2),
 QPoint(16, 4),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(17, 0),
 QPoint(17, 2),
 QPoint(17, 4),
 QPoint(17, 5),
 QPoint(18, 0),
 QPoint(18, 2),
 QPoint(18, 4),
 QPoint(18, 5),
 QPoint(18, 7),
 QPoint(19, 0),
 QPoint(19, 2),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 7),
 QPoint(20, 0),
 QPoint(20, 2),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 2),
 QPoint(21, 4),
 QPoint(21, 5),
 QPoint(21, 6),
 QPoint(21, 7),
 QPoint(21, 8),
 QPoint(21, 9),
 QPoint(22, 0),
 QPoint(22, 2),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 7),
 QPoint(22, 8),
 QPoint(22, 9),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 2),
 QPoint(23, 3),
 QPoint(23, 4),
 QPoint(23, 5),
 QPoint(23, 6),
 QPoint(23, 7),
 QPoint(23, 8),
 QPoint(23, 9),
 QPoint(24, 0),
 QPoint(24, 1),
 QPoint(24, 2),
 QPoint(24, 3),
 QPoint(24, 4),
 QPoint(24, 5),
 QPoint(24, 6),
 QPoint(24, 7),
 QPoint(24, 8),
 QPoint(25, 1),
 QPoint(25, 2),
 QPoint(25, 3),
 QPoint(25, 4),
 QPoint(25, 5)
]
jinglingRedPoints = [
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(0, 9),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(1, 9),
 QPoint(2, 0),
 QPoint(2, 1),
 QPoint(2, 2),
 QPoint(2, 3),
 QPoint(2, 4),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(2, 8),
 QPoint(2, 9),
 QPoint(3, 4),
 QPoint(3, 7),
 QPoint(3, 8),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(4, 9),
 QPoint(5, 0),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7),
 QPoint(5, 8),
 QPoint(5, 9),
 QPoint(6, 0),
 QPoint(6, 1),
 QPoint(6, 2),
 QPoint(6, 3),
 QPoint(6, 4),
 QPoint(6, 5),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(6, 8),
 QPoint(6, 9),
 QPoint(7, 0),
 QPoint(7, 1),
 QPoint(7, 2),
 QPoint(7, 3),
 QPoint(7, 4),
 QPoint(7, 5),
 QPoint(7, 6),
 QPoint(7, 7),
 QPoint(7, 8),
 QPoint(7, 9),
 QPoint(8, 0),
 QPoint(8, 1),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 4),
 QPoint(8, 5),
 QPoint(8, 6),
 QPoint(8, 7),
 QPoint(8, 8),
 QPoint(8, 9),
 QPoint(9, 0),
 QPoint(9, 1),
 QPoint(9, 2),
 QPoint(9, 3),
 QPoint(9, 4),
 QPoint(9, 5),
 QPoint(9, 6),
 QPoint(9, 7),
 QPoint(9, 8),
 QPoint(9, 9),
 QPoint(10, 0),
 QPoint(10, 1),
 QPoint(10, 2),
 QPoint(10, 3),
 QPoint(10, 4),
 QPoint(10, 5),
 QPoint(10, 6),
 QPoint(10, 7),
 QPoint(10, 8),
 QPoint(10, 9),
 QPoint(11, 0),
 QPoint(11, 2),
 QPoint(11, 3),
 QPoint(11, 4),
 QPoint(11, 5),
 QPoint(11, 6),
 QPoint(11, 7),
 QPoint(11, 8),
 QPoint(11, 9),
 QPoint(16, 2),
 QPoint(18, 2),
 QPoint(18, 4),
 QPoint(19, 2),
 QPoint(19, 4),
 QPoint(20, 2),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 7),
 QPoint(21, 2),
 QPoint(21, 4),
 QPoint(21, 9),
 QPoint(22, 2),
 QPoint(22, 4),
 QPoint(23, 2),
 QPoint(23, 4),
 QPoint(23, 8),
 QPoint(24, 0),
 QPoint(24, 1),
 QPoint(24, 2),
 QPoint(24, 3),
 QPoint(24, 4),
 QPoint(24, 5),
 QPoint(25, 0),
 QPoint(25, 2),
 QPoint(25, 3),
 QPoint(25, 4),
 QPoint(25, 5)
]
louluoRedPoints = [
 QPoint(0, 2),
 QPoint(0, 3),
 QPoint(0, 4),
 QPoint(0, 5),
 QPoint(0, 6),
 QPoint(0, 7),
 QPoint(0, 8),
 QPoint(0, 9),
 QPoint(1, 2),
 QPoint(1, 3),
 QPoint(1, 4),
 QPoint(1, 5),
 QPoint(1, 6),
 QPoint(1, 7),
 QPoint(1, 8),
 QPoint(1, 9),
 QPoint(2, 2),
 QPoint(2, 4),
 QPoint(2, 5),
 QPoint(2, 6),
 QPoint(2, 7),
 QPoint(3, 2),
 QPoint(3, 4),
 QPoint(3, 5),
 QPoint(3, 6),
 QPoint(3, 7),
 QPoint(3, 8),
 QPoint(3, 9),
 QPoint(4, 2),
 QPoint(4, 3),
 QPoint(4, 4),
 QPoint(4, 6),
 QPoint(4, 7),
 QPoint(4, 8),
 QPoint(4, 9),
 QPoint(5, 2),
 QPoint(5, 3),
 QPoint(5, 4),
 QPoint(5, 5),
 QPoint(5, 6),
 QPoint(5, 7),
 QPoint(5, 8),
 QPoint(5, 9),
 QPoint(6, 2),
 QPoint(6, 3),
 QPoint(6, 4),
 QPoint(6, 5),
 QPoint(6, 6),
 QPoint(6, 7),
 QPoint(6, 8),
 QPoint(6, 9),
 QPoint(7, 2),
 QPoint(7, 3),
 QPoint(7, 4),
 QPoint(7, 5),
 QPoint(7, 6),
 QPoint(7, 7),
 QPoint(7, 8),
 QPoint(7, 9),
 QPoint(8, 2),
 QPoint(8, 3),
 QPoint(8, 4),
 QPoint(8, 5),
 QPoint(8, 6),
 QPoint(8, 7),
 QPoint(8, 8),
 QPoint(9, 2),
 QPoint(9, 3),
 QPoint(9, 4),
 QPoint(9, 5),
 QPoint(9, 6),
 QPoint(9, 7),
 QPoint(10, 2),
 QPoint(10, 5),
 QPoint(10, 7),
 QPoint(13, 6),
 QPoint(13, 7),
 QPoint(15, 2),
 QPoint(15, 3),
 QPoint(15, 6),
 QPoint(15, 7),
 QPoint(15, 8),
 QPoint(15, 9),
 QPoint(16, 2),
 QPoint(16, 3),
 QPoint(16, 4),
 QPoint(16, 5),
 QPoint(16, 6),
 QPoint(16, 7),
 QPoint(16, 8),
 QPoint(16, 9),
 QPoint(17, 2),
 QPoint(17, 8),
 QPoint(18, 1),
 QPoint(18, 2),
 QPoint(18, 3),
 QPoint(18, 4),
 QPoint(18, 7),
 QPoint(18, 8),
 QPoint(19, 2),
 QPoint(19, 3),
 QPoint(19, 4),
 QPoint(19, 5),
 QPoint(19, 6),
 QPoint(19, 7),
 QPoint(20, 0),
 QPoint(20, 1),
 QPoint(20, 2),
 QPoint(20, 3),
 QPoint(20, 4),
 QPoint(20, 5),
 QPoint(20, 6),
 QPoint(20, 7),
 QPoint(20, 8),
 QPoint(20, 9),
 QPoint(21, 0),
 QPoint(21, 2),
 QPoint(21, 3),
 QPoint(21, 4),
 QPoint(21, 5),
 QPoint(21, 6),
 QPoint(21, 8),
 QPoint(21, 9),
 QPoint(22, 0),
 QPoint(22, 2),
 QPoint(22, 3),
 QPoint(22, 4),
 QPoint(22, 5),
 QPoint(22, 6),
 QPoint(22, 8),
 QPoint(22, 9),
 QPoint(23, 0),
 QPoint(23, 1),
 QPoint(23, 2),
 QPoint(23, 3),
 QPoint(23, 4),
 QPoint(23, 5),
 QPoint(23, 6),
 QPoint(23, 8),
 QPoint(23, 9),
 QPoint(24, 0),
 QPoint(24, 2),
 QPoint(24, 3),
 QPoint(24, 4),
 QPoint(24, 5),
 QPoint(24, 6),
 QPoint(24, 7),
 QPoint(24, 8),
 QPoint(24, 9),
 QPoint(25, 0),
 QPoint(25, 1),
 QPoint(25, 2),
 QPoint(25, 3),
 QPoint(25, 4),
 QPoint(25, 5),
 QPoint(25, 6),
 QPoint(25, 7)
]

def getColorFromFrame(frame, point):
    try:
        pixel_bgr = frame[point.y(), point.x()]
        return QColor(pixel_bgr[2], pixel_bgr[1], pixel_bgr[0])
    except Exception as e:
        logger.debug(f"getColorFromFrame异常: {e}")
        return QColor()


def isWhiteTextColor(color, value=200):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > value:
        if green > value:
            if blue > value:
                return True
    return False
    return None


def isBlackTextColor(color, value=80):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < value:
        if green < value:
            if blue < value:
                return True
    return False
    return None


def isDarkWhiteColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 135:
        if green > 150:
            if blue > 150:
                return True
    return False
    return None


def __isPositionNumColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red >= 100:
        if green > 125:
            if blue > 135:
                return True
    return False
    return None


def isWhiteZaiColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 110:
        if green > 110:
            if blue > 100:
                return True
    return False
    return None


def culNewMobileXOffset(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    newMobileXOffset = 0
    for x in range(13):
        isYAllWhite = True
        for y in range(7):
            curColor = getColorFromFrame(frame, QPoint(x + 78, y + 8))
            if curColor.red() > 120 and curColor.green() > 140 and curColor.blue() > 160:
                continue
            isYAllWhite = False
            break
        else:
            if isYAllWhite:
                newMobileXOffset = x + 78 - 42
                break
    return newMobileXOffset


def matchPointColors(frame, pointsList, texts, colorFuc, offsetList=[QPoint(0, 0)], errorSimilar=0.1, oneTextSimilarMap=None):
    resText = None
    for index in range(len(pointsList)):
        points = pointsList[index]
        okOffset = None
        for offsetPoint in offsetList:
            errorCount = 0
            similar = errorSimilar
            if texts[index] == "东海湾" or texts[index] == "东海渊":
                similar = 0.05
            if oneTextSimilarMap:
                if texts[index] in oneTextSimilarMap:
                    similar = oneTextSimilarMap[texts[index]]
            for point in points:
                x = offsetPoint.x() + point.x()
                y = offsetPoint.y() + point.y()
                color = getColorFromFrame(frame, QPoint(x, y))
                isColorOk = colorFuc(color)
                if not isColorOk:
                    errorCount += 1
                if errorCount / len(points) > similar:
                    break
            if errorCount / len(points) <= similar:
                resText = texts[index]
                okOffset = offsetPoint
                break
        if okOffset is not None:
            break
    return resText


def getType1Num(frame, startX, endX, startY, colorFunc=__isPositionNumColor):
    resultNumStr = ""
    numLen = round((endX - startX) / 7.5)
    for numTh in range(numLen):
        for index in range(len(type1NumPointsList)):
            points = type1NumPointsList[index]
            num = numResList[index]
            rightOffset = None
            for offset in OFFSET_SEQUENCE0_1:
                isOk = True
                wrongCount = 0
                for point in points:
                    x = startX + offset.x() + 8 * numTh + point.x()
                    y = startY + offset.y() + point.y()
                    if x > endX:
                        break
                    color = getColorFromFrame(frame, QPoint(x, y))
                    if not colorFunc(color):
                        wrongCount += 1
                    if wrongCount > 0:
                        isOk = False
                        break
                if isOk:
                    if numTh == 0:
                        resultNumStr = str(num)
                    else:
                        resultNumStr += str(num)
                    rightOffset = offset
                    break
            if rightOffset is not None:
                break
    else:
        if len(resultNumStr) < numLen or resultNumStr == "":
            cv2.imwrite("./getType1Num_error.png", frame)
            return
        return resultNumStr


def isShowPopColorDK(deviceId, withClickDismiss=False):
    if _isShowPopColor(deviceId):
        if withClickDismiss:
            if _isShowPopColor(deviceId):
                click(deviceId, QPoint(400, 224))
                time.sleep(random.uniform(0.5, 0.8))
        return True
    return False
    return None


def _isShowPopColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    for x in range(resultPopShowPointsAvoidChengJiu1[0].x(), resultPopShowPointsAvoidChengJiu1[1].x()):
        for y in range(resultPopShowPointsAvoidChengJiu1[0].y(), resultPopShowPointsAvoidChengJiu1[1].y()):
            color = getColorFromFrame(frame, QPoint(x, y))
            if not _isResultPopColor(color):
                return False
    for x in range(resultPopShowPointsAvoidChengJiu2[0].x(), resultPopShowPointsAvoidChengJiu2[1].x()):
        for y in range(resultPopShowPointsAvoidChengJiu2[0].y(), resultPopShowPointsAvoidChengJiu2[1].y()):
            color = getColorFromFrame(frame, QPoint(x, y))
            if not _isResultPopColor(color):
                return False
    return True


def _isResultPopColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if 12 < red < 32:
        if 32 < green < 52:
            if 44 < blue < 64:
                return True
    return False
    return None


def _isResultBtnColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 70:
        if 58 < green < 98:
            if 81 < blue < 121:
                return True
    return False
    return None


def isShowHideEnter(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideEnterShowPoints:
        color = getColorFromFrame(frame, point)
        if _isHideEnterColor(color):
            okPoint += 1
    if okPoint >= len(hideEnterShowPoints) * 0.7:
        return True
    return False
    return None


def _isHideEnterColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 170:
        if green > 140:
            if blue > 80:
                return True
    return False
    return None


def isOpenHidePlayerColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hidePlayerOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1
    if okPoint >= len(hidePlayerOpenPoints) * 0.8:
        return True
    return False
    return None


def isOpenHideTanWeiColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideTanweiOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1
    if okPoint >= len(hideTanweiOpenPoints) * 0.8:
        return True
    return False
    return None


def isOpenHideJieMianColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    okPoint = 0
    for point in hideJiemianOpenPoints:
        color = getColorFromFrame(frame, point)
        if _isHideOpenColor(color):
            okPoint += 1
    if okPoint >= len(hideJiemianOpenPoints) * 0.8:
        return True
    return False
    return None


def _isHideOpenColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 160:
        if green > 190:
            if blue > 200:
                return True
    return False
    return None


def isShowRoleAvatar(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    for i in range(30):
        if const.gameType == "畅玩服":
            color = getColorFromFrame(frame, QPoint(706 + i, 0))
            if 55 < color.red() < 85 and 70 < color.green() < 115 and 70 < color.blue() < 115:
                continue
            if 115 < color.red() < 150 and 145 < color.green() < 185 and 145 < color.blue() < 185:
                continue
            return False
        elif const.gameType == "点卡服":
            color = getColorFromFrame(frame, QPoint(710 + i, 1))
            if 45 < color.red() < 115 and 75 < color.green() < 140 and 85 < color.blue() < 180:
                continue
            return False
    return True


def getPkgPointList(firstCenterPoint):
    pkgPoints = []
    for i in range(20):
        row = i // 5
        colum = i % 5
        targetPoint = firstCenterPoint + QPoint(57 * colum, 56 * row)
        pkgPoints.append(targetPoint)
    else:
        return pkgPoints


def getHasProductPoints(deviceId, firstCenterPoint=QPoint(285, 129), isCareForbid=True):
    frame = scrcpyUtil.getFrame(deviceId)
    hasProductPoints = []
    centerPoints = getPkgPointList(firstCenterPoint)
    for index in range(len(centerPoints)):
        if not isEmptyProduct(frame, centerPoints[index], index=index, isCareForbid=isCareForbid):
            hasProductPoints.append(centerPoints[index])
    return hasProductPoints


def isEmptyProduct(frame, centerP, emptyColor=QColor(185, 173, 216, 255), index=-1, isCareForbid=True):
    isEmpty = True
    radius1 = 45
    radius2 = 45
    if index == 0 or index == 19:
        radius1 = 8
    elif index == 4 or index == 15:
        radius2 = 8
    for i in range(radius1):
        topLeftToBottomRightX = centerP.x() + i - radius1 / 2
        topLeftToBottomRightY = centerP.y() + i - radius1 / 2
        topLeftToBottomRightColor = getColorFromFrame(frame, QPoint(topLeftToBottomRightX, topLeftToBottomRightY))
        if __isEmptyColor(topLeftToBottomRightColor, emptyColor) is False:
            isEmpty = False
            break
    for i in range(radius2):
        bottomLeftToTopRightX = centerP.x() + i - radius2 / 2
        bottomLeftToTopRightY = centerP.y() - i + radius2 / 2
        bottomLeftToTopRightColor = getColorFromFrame(frame, QPoint(bottomLeftToTopRightX, bottomLeftToTopRightY))
        if __isEmptyColor(bottomLeftToTopRightColor, emptyColor) is False:
            isEmpty = False
            break
    return isEmpty or isCareForbid and isForbidProduct(frame, centerP)


def isForbidProduct(frame, centerP):
    redPoints = [
        QPoint(11, -7), QPoint(8, -4), QPoint(4, 0), QPoint(1, 3), QPoint(-3, 7),
        QPoint(-7, 11), QPoint(-10, 14), QPoint(-7, 17), QPoint(-5, 19), QPoint(-2, 19),
        QPoint(4, 19), QPoint(9, 17), QPoint(15, 13), QPoint(17, 10), QPoint(18, 5),
        QPoint(18, 0), QPoint(18, -4), QPoint(16, -8),
    ]
    redCount = 0
    for redP in redPoints:
        color = getColorFromFrame(frame, centerP + redP)
        if __isForbidColor(color):
            redCount += 1
    return redCount >= len(redPoints) * 0.85


def __isEmptyColor(color, emptyColor):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if abs(red - emptyColor.red()) < 20:
        if abs(green - emptyColor.green()) < 20:
            if abs(blue - emptyColor.blue()) < 20:
                return True
    return False
    return None


def __isForbidColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 110:
        if green < 145:
            if blue < 150:
                return True
    return False
    return None


def isPageBlackColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red < 110:
        if green < 120:
            if blue < 140:
                return True
    return False
    return None


def waitCropFrameChange(frame1, deviceId, left, top, crop_width, crop_height, perT=0.5, totalT=10):
    isChange = False
    waitT = 0
    roi1 = frame1[top:top + crop_height, left:left + crop_width]
    while True:
        frame2 = scrcpyUtil.getFrame(deviceId)
        roi2 = frame2[top:top + crop_height, left:left + crop_width]
        isSame = isframeSame(roi1, roi2)
        if not isSame:
            time.sleep(perT)
            isChange = True
            break
        time.sleep(perT)
        waitT += perT
        if waitT > totalT:
            break
    return isChange


def isPointColor(frame, point, color, rongCuo=20):
    curColor = getColorFromFrame(frame, point)
    if abs(color.red() - curColor.red()) < rongCuo:
        if abs(color.green() - curColor.green()) < rongCuo:
            if abs(color.blue() - curColor.blue()) < rongCuo:
                return True
    return False


def isLineColor(frame, startP, color, type="all", direct="h", step=3, distance=20, rongCuo=20):
    if direct == "h":
        for x in range(startP.x(), startP.x() + distance, step):
            curColor = getColorFromFrame(frame, QPoint(x, startP.y()))
            if type == "all":
                if abs(color.red() - curColor.red()) < rongCuo and abs(color.green() - curColor.green()) < rongCuo and abs(color.blue() - curColor.blue()) < rongCuo:
                    pass
                else:
                    return False
            elif type == "one" and abs(color.red() - curColor.red()) < rongCuo and abs(color.green() - curColor.green()) < rongCuo and abs(color.blue() - curColor.blue()) < rongCuo:
                return True
    elif direct == "v":
        for y in range(startP.y(), startP.y() + distance, step):
            curColor = getColorFromFrame(frame, QPoint(startP.x(), y))
            if type == "all":
                if abs(color.red() - curColor.red()) < rongCuo and abs(color.green() - curColor.green()) < rongCuo and abs(color.blue() - curColor.blue()) < rongCuo:
                    pass
                else:
                    return False
            elif type == "one" and abs(color.red() - curColor.red()) < rongCuo and abs(color.green() - curColor.green()) < rongCuo and abs(color.blue() - curColor.blue()) < rongCuo:
                return True
    if type == "all":
        return True
    return False


def isAutoChuanSongColor(deviceId):
    frame = scrcpyUtil.getFrame(deviceId)
    for i in range(285, 295):
        for j in range(310, 320):
            color = getColorFromFrame(frame, QPoint(i, j))
            if color.red() > 100 or color.green() > 100 or color.blue() > 100:
                return False
    okCount = 0
    for point in ziDongTextPoints:
        color = getColorFromFrame(frame, point)
        if color.red() > 150 and color.green() > 150 and color.blue() > 150:
            okCount += 1
    isShowAuto = okCount >= len(ziDongTextPoints) * 0.9
    if isShowAuto:
        time.sleep(15)
    return isShowAuto


def isJumpPageGray(deviceId, topPoint=QPoint(182, 390)):
    frame = scrcpyUtil.getFrame(deviceId)
    for y in range(15):
        if not isPointColor(frame, QPoint(topPoint.x() - 5, topPoint.y() + y), QColor(62, 62, 62), rongCuo=10):
            return False
    return True


def isNeedWuYiColor(deviceId):
    return not isPointColor((scrcpyUtil.getFrame(deviceId)), (QPoint(586, 30)), (QColor(241, 144, 26)), rongCuo=15)
    return None


def findTextPosition(deviceId, textPoints, left, top, width, height, isColorFunc=None, curframe=None, rongCuo=0.1):
    frame = None
    if curframe is not None:
        frame = curframe
    else:
        frame = scrcpyUtil.getFrame(deviceId)
    for y in range(height):
        for x in range(width):
            xTMP = left + x
            yTMP = top + y
            color1 = getColorFromFrame(frame, QPoint(xTMP, yTMP))
            isOkColor = isColorFunc(color1)
            if isOkColor:
                isAllColorOk = True
                wrongCount = 0

    for textP in textPoints:
        tmpX = xTMP + textP.x()
        tmpY = yTMP + textP.y()
        color2 = getColorFromFrame(frame, QPoint(tmpX, tmpY))
        if isColorFunc(color2) is False:
            wrongCount += 1
        if wrongCount >= len(textPoints) * rongCuo:
            isAllColorOk = False
            break
        if isAllColorOk:
            isBgOk = True
            bgPoints = []
            bgOkPercent = 0.85
            tip = ""
            if textPoints == baobaoRedPoints:
                bgPoints = baobaoRedPoints_Bg
                bgOkPercent = 0.5
                tip = "红色宝宝"
            else:
                if textPoints == baobaoBluePoints:
                    bgPoints = baobaoBluePoints_Bg
                    tip = "蓝色宝宝"
                else:
                    if textPoints == huyouRedPoints:
                        bgPoints = huyouRedPoints_Bg
                        tip = "红色护佑"
                    else:
                        if textPoints == toulingRedPoints:
                            bgPoints = toulingRedPoints_Bg
                            tip = "红色头领"
                        else:
                            if textPoints == baozhaRedPoints:
                                bgPoints = baozhaRedPoints_Bg
                                bgOkPercent = 0.75
                                tip = "红色爆炸"
                            else:
                                if textPoints == jingyingRedPoints:
                                    bgPoints = jingyingRedPoints_Bg
                                    tip = "红色精英"
                                else:
                                    if textPoints == zaiTextPoints:
                                        bgPoints = zaiTextPoints_Bg
                                        bgOkPercent = 0.7
                                        tip = "四小人在"
            if len(bgPoints) > 0:
                bgOkCount = 0
                for bgP in bgPoints:
                    bgColor = getColorFromFrame(frame, QPoint(bgP.x() + xTMP, bgP.y() + yTMP))
                    if isColorFunc(bgColor) is False:
                        bgOkCount += 1

                if bgOkCount / len(bgPoints) < bgOkPercent:
                    isBgOk = False
            if isBgOk:
                return QPoint(xTMP, yTMP)
    else:
        return


def isRedBaoBaoTextColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if red > 115:
        if green < 70:
            if blue < 70:
                return True
    return False
    return None


def isBlueBaoBaoTextColor(color):
    red = color.red()
    green = color.green()
    blue = color.blue()
    if 150 > red > 80:
        if 100 < green < 185:
            if 105 < blue < 200:
                return True
    return False
    return None


def isFourPersonWhiteTxtColor(color):
    return color.red() > 95 and color.green() > 95 and color.blue() > 95
    return None

