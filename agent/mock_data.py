"""模拟数据：商品库、订单库、知识库"""

# ========== 商品库 ==========
PRODUCTS = [
    {"id": "P001", "name": "iPhone 15 Pro Max", "category": "手机", "price": 9999, "stock": 50,
     "description": "Apple 旗舰手机，A17 Pro 芯片，钛金属设计，48MP 主摄像头"},
    {"id": "P002", "name": "华为 Mate 60 Pro", "category": "手机", "price": 6999, "stock": 30,
     "description": "麒麟 9000S 芯片，卫星通话功能，XMAGE 影像系统"},
    {"id": "P003", "name": "小米 14 Ultra", "category": "手机", "price": 5999, "stock": 80,
     "description": "骁龙 8 Gen 3，徕卡光学镜头，2K LTPO 屏幕"},
    {"id": "P004", "name": "Sony WH-1000XM5", "category": "耳机", "price": 2699, "stock": 120,
     "description": "旗舰降噪耳机，30 小时续航，多点连接"},
    {"id": "P005", "name": "MacBook Pro 14", "category": "笔记本", "price": 14999, "stock": 25,
     "description": "M3 Pro 芯片，Liquid Retina XDR 屏幕，18 小时续航"},
    {"id": "P006", "name": "iPad Air M2", "category": "平板", "price": 4799, "stock": 60,
     "description": "M2 芯片，10.9 英寸 Liquid Retina 屏幕，支持 Apple Pencil"},
    {"id": "P007", "name": "Nike Air Max 270", "category": "运动鞋", "price": 1099, "stock": 200,
     "description": "经典气垫运动鞋，舒适缓震，多彩配色"},
    {"id": "P008", "name": "戴森 V15 Detect", "category": "家电", "price": 4990, "stock": 40,
     "description": "智能无绳吸尘器，激光探测灰尘，LCD 显示颗粒数据"},
    {"id": "P009", "name": "优衣库 极暖内衣套装", "category": "服饰", "price": 199, "stock": 500,
     "description": "HEATTECH 科技面料，轻薄保暖，吸湿发热"},
    {"id": "P010", "name": "Switch OLED", "category": "游戏机", "price": 2599, "stock": 45,
     "description": "7 英寸 OLED 屏幕，64GB 内存，可桌面/掌机/TV 三模式"},
    {"id": "P011", "name": "Apple Watch Ultra 2", "category": "智能手表", "price": 6499, "stock": 35,
     "description": "钛金属表壳，双频 GPS，100 米防水，S9 芯片，最长 72 小时续航"},
    {"id": "P012", "name": "索尼 A7M4 微单相机", "category": "相机", "price": 16999, "stock": 15,
     "description": "全画幅 3300 万像素，实时眼部对焦，4K 60fps 视频录制"},
    {"id": "P013", "name": "ROG 幻 16 游戏本", "category": "笔记本", "price": 12999, "stock": 20,
     "description": "i9-13900H + RTX 4070，16 英寸 2.5K 240Hz 屏，DDR5 16GB"},
    {"id": "P014", "name": "三星 Galaxy Tab S9 Ultra", "category": "平板", "price": 8999, "stock": 22,
     "description": "14.6 英寸 Super AMOLED 屏，骁龙 8 Gen 2，12GB+256GB，含 S Pen"},
    {"id": "P015", "name": "AirPods Pro 2", "category": "耳机", "price": 1899, "stock": 150,
     "description": "H2 芯片，自适应降噪，个性化空间音频，USB-C 充电盒"},
    {"id": "P016", "name": "HHKB Professional HYBRID Type-S", "category": "键盘", "price": 2699, "stock": 30,
     "description": "静电容键盘，蓝牙+USB-C 双模，静音版，PBT 键帽"},
    {"id": "P017", "name": "LG 27GP950 4K 显示器", "category": "显示器", "price": 5499, "stock": 18,
     "description": "27 英寸 Nano IPS，4K 160Hz，HDMI 2.1，HDR600，1ms 响应"},
    {"id": "P018", "name": "大疆 Mini 4 Pro 无人机", "category": "无人机", "price": 4788, "stock": 25,
     "description": "249g 轻巧机身，4K/60fps HDR 视频，全向避障，34 分钟续航"},
    {"id": "P019", "name": "Marshall Stanmore III 音箱", "category": "音箱", "price": 3699, "stock": 40,
     "description": "经典摇滚外观，蓝牙 5.2，动态响度调节，支持多房间播放"},
    {"id": "P020", "name": "石头 G20 扫拖机器人", "category": "家电", "price": 5999, "stock": 55,
     "description": "双旋臂拖布，自动集尘洗拖烘，LDS 激光导航，5500Pa 大吸力"},
    {"id": "P021", "name": "Lululemon Align 瑜伽裤", "category": "服饰", "price": 850, "stock": 300,
     "description": "Nulu 面料，裸感穿着体验，高腰设计，四向拉伸，多色可选"},
    {"id": "P022", "name": "飞利浦 S9000 Prestige 电动剃须刀", "category": "个护电器", "price": 2999, "stock": 70,
     "description": "纳米刀片，干湿双剃，无线充电底座，智能清洁系统"},
    {"id": "P023", "name": "Keep C1 Pro 动感单车", "category": "健身器材", "price": 2999, "stock": 28,
     "description": "磁控静音飞轮，APP 互联直播课，心率臂带监测，100 档阻力"},
    {"id": "P024", "name": "雅诗兰黛 小棕瓶精华", "category": "美妆护肤", "price": 590, "stock": 400,
     "description": "第七代特润修护肌透精华露 50ml，夜间修护，淡化细纹"},
    {"id": "P025", "name": "佳能 SELPHY CP1500 照片打印机", "category": "打印机", "price": 1199, "stock": 65,
     "description": "热升华技术，4x6 寸照片打印，Wi-Fi 直连，防水防指纹"},
    {"id": "P026", "name": "Kindle Paperwhite 5", "category": "电子书", "price": 1049, "stock": 90,
     "description": "6.8 英寸电子墨水屏，冷暖色温调节，IPX8 防水，16GB 存储"},
    {"id": "P027", "name": "小米 Civi 4 Pro", "category": "手机", "price": 3299, "stock": 100,
     "description": "骁龙 8s Gen 3，徕卡三摄，1.5K OLED 曲面屏，4700mAh 电池"},
    {"id": "P028", "name": "Herman Miller Aeron 人体工学椅", "category": "家具", "price": 12800, "stock": 10,
     "description": "经典网布座椅，PostureFit SL 腰托，8Z Pellicle 悬挂系统"},
    {"id": "P029", "name": "松下 EH-NA0J 吹风机", "category": "个护电器", "price": 1699, "stock": 80,
     "description": "纳米水离子技术，智能温控护发，快速干发，折叠便携设计"},
    {"id": "P030", "name": "Bose SoundLink Max 音箱", "category": "音箱", "price": 2999, "stock": 50,
     "description": "便携蓝牙音箱，震撼低音，IP67 防尘防水，20 小时续航"}
,
    {'id': 'P031', 'name': '海南网纹瓜', 'category': '水果', 'price': 39, 'stock': 100, 'description': '单个约3斤，清甜多汁，现摘直发'},
    {'id': 'P032', 'name': '智利车厘子JJJ级', 'category': '水果', 'price': 299, 'stock': 100, 'description': '2.5kg原箱，当季新鲜，脆甜可口'},
    {'id': 'P033', 'name': '丹东红颜草莓', 'category': '水果', 'price': 88, 'stock': 100, 'description': '精品大果，奶香浓郁，产地直供'},
    {'id': 'P034', 'name': '泰国金枕榴莲', 'category': '水果', 'price': 198, 'stock': 100, 'description': '带壳约4-5斤，软糯香甜，包四房肉'},
    {'id': 'P035', 'name': '阳光玫瑰葡萄', 'category': '水果', 'price': 69, 'stock': 100, 'description': '2斤装，无籽脆甜，玫瑰香气'},
    {'id': 'P036', 'name': '佳沛阳光金奇异果', 'category': '水果', 'price': 129, 'stock': 100, 'description': '特大果22粒装，维C满满，口感细腻'},
    {'id': 'P037', 'name': '新疆库尔勒香梨', 'category': '水果', 'price': 35, 'stock': 100, 'description': '5斤特级果，皮薄核小，脆甜化渣'},
    {'id': 'P038', 'name': '突尼斯软籽石榴', 'category': '水果', 'price': 45, 'stock': 100, 'description': '5斤装，大果，籽软可食，汁水丰盈'},
    {'id': 'P039', 'name': '广西武鸣沃柑', 'category': '水果', 'price': 39, 'stock': 100, 'description': '5斤精选果，甜度高，果肉饱满'},
    {'id': 'P040', 'name': '越南进口青芒果', 'category': '水果', 'price': 29, 'stock': 100, 'description': '5斤装，可生食或催熟，酸甜开胃'},
    {'id': 'P041', 'name': '四川攀枝花凯特芒', 'category': '水果', 'price': 49, 'stock': 100, 'description': '5斤大果，果肉厚实，纤维少'},
    {'id': 'P042', 'name': '烟台红富士苹果', 'category': '水果', 'price': 55, 'stock': 100, 'description': '80mm大果12个，脆甜可口，果香浓郁'},
    {'id': 'P043', 'name': '四川安岳黄柠檬', 'category': '水果', 'price': 19, 'stock': 100, 'description': '3斤装，果大皮薄，泡水佳品'},
    {'id': 'P044', 'name': '海南金钻凤梨', 'category': '水果', 'price': 45, 'stock': 100, 'description': '2个装，不用泡盐水，纯甜无酸味'},
    {'id': 'P045', 'name': '福建平和蜜柚', 'category': '水果', 'price': 39, 'stock': 100, 'description': '红心柚2个装，酸甜多汁，果肉红润'},
    {'id': 'P046', 'name': '云南蒙自石榴', 'category': '水果', 'price': 59, 'stock': 100, 'description': '软籽大果，单果400g+，甜度高'},
    {'id': 'P047', 'name': '陕西眉县徐香猕猴桃', 'category': '水果', 'price': 29, 'stock': 100, 'description': '30枚装，绿心酸甜，果肉细腻'},
    {'id': 'P048', 'name': '山东秋月梨', 'category': '水果', 'price': 68, 'stock': 100, 'description': '5斤礼盒装，水分充足，清甜无渣'},
    {'id': 'P049', 'name': '海南妃子笑荔枝', 'category': '水果', 'price': 89, 'stock': 100, 'description': '3斤顺丰空运，核小肉厚，甜度极高'},
    {'id': 'P050', 'name': '秘鲁进口蓝莓', 'category': '水果', 'price': 99, 'stock': 100, 'description': '18mm+特大果 4盒装，果粉完整，护眼佳品'},
    {'id': 'P051', 'name': '波士顿大龙虾', 'category': '海鲜', 'price': 168, 'stock': 100, 'description': '单只500g左右，鲜活发货，肉质紧实'},
    {'id': 'P052', 'name': '俄罗斯帝王蟹', 'category': '海鲜', 'price': 899, 'stock': 100, 'description': '鲜活/熟冻随机，约1.5kg，蟹腿肉饱满'},
    {'id': 'P053', 'name': '鲜活基围虾', 'category': '海鲜', 'price': 68, 'stock': 100, 'description': '1斤装，冷链直达，适合白灼/香辣'},
    {'id': 'P054', 'name': '大连鲜活鲍鱼', 'category': '海鲜', 'price': 99, 'stock': 100, 'description': '10只装（10头），煮汤生煎皆宜'},
    {'id': 'P055', 'name': '獐子岛蒜蓉粉丝扇贝', 'category': '海鲜', 'price': 49, 'stock': 100, 'description': '半壳20只，冷冻半成品，微波加热即食'},
    {'id': 'P056', 'name': '阳澄湖大闸蟹', 'category': '海鲜', 'price': 399, 'stock': 100, 'description': '4.0两公/3.0两母各4只，蟹黄肥美，含蟹具'},
    {'id': 'P057', 'name': '智利三文鱼刺身', 'category': '海鲜', 'price': 128, 'stock': 100, 'description': '500g中段切片，配芥末酱油，入口即化'},
    {'id': 'P058', 'name': '深海银鳕鱼切片', 'category': '海鲜', 'price': 158, 'stock': 100, 'description': '400g，无小刺，适合宝宝辅食/香煎'},
    {'id': 'P059', 'name': '冷冻厄瓜多尔白虾', 'category': '海鲜', 'price': 88, 'stock': 100, 'description': '净重1.8kg/盒，个大肉弹，烹饪百搭'},
    {'id': 'P060', 'name': '鲜活兰花蟹', 'category': '海鲜', 'price': 118, 'stock': 100, 'description': '2斤装，肉干甜，适合清蒸或姜葱炒'},
    {'id': 'P061', 'name': '大连野生海参', 'category': '海鲜', 'price': 499, 'stock': 100, 'description': '即食500g，参刺挺拔，滋补佳品'},
    {'id': 'P062', 'name': '北极甜虾', 'category': '海鲜', 'price': 79, 'stock': 100, 'description': '90-120只/kg生鲜冷冻，带籽鲜甜'},
    {'id': 'P063', 'name': '野生东星斑', 'category': '海鲜', 'price': 299, 'stock': 100, 'description': '整条处理后约600g，清蒸首选，肉质细嫩'},
    {'id': 'P064', 'name': '宁德大黄鱼', 'category': '海鲜', 'price': 59, 'stock': 100, 'description': '2条装，肉质蒜瓣状，红烧或清蒸佳'},
    {'id': 'P065', 'name': '青岛大虾干', 'category': '海鲜', 'price': 65, 'stock': 100, 'description': '250g，原汁原味无盐添加，煲汤炒菜'},
    {'id': 'P066', 'name': '蒜香烤生蚝', 'category': '海鲜', 'price': 89, 'stock': 100, 'description': '烤肉店同款，半壳30只加蒜蓉酱，烤箱专用'},
    {'id': 'P067', 'name': '北海道生鲜干贝', 'category': '海鲜', 'price': 199, 'stock': 100, 'description': '500g刺身级新鲜带子，鲜甜软嫩'},
    {'id': 'P068', 'name': '阿根廷红虾', 'category': '海鲜', 'price': 129, 'stock': 100, 'description': '2kg原箱L1级特大虾，适合刺身或碳烤'},
    {'id': 'P069', 'name': '野生大墨鱼', 'category': '海鲜', 'price': 55, 'stock': 100, 'description': '整只约800g，肉厚Q弹，适合爆炒'},
    {'id': 'P070', 'name': '新鲜海带结', 'category': '海鲜', 'price': 15, 'stock': 100, 'description': '1000g，凉拌或炖汤，补碘好食材'},
    {'id': 'P071', 'name': '扬州碎金炒饭', 'category': '主食/炒饭', 'price': 28, 'stock': 100, 'description': '300g单人份，虾仁、叉烧、鸡蛋，料足味美'},
    {'id': 'P072', 'name': '腊味排骨煲仔饭', 'category': '主食/炒饭', 'price': 35, 'stock': 100, 'description': '自热米饭，广式腊肠与软烂排骨，锅巴焦香'},
    {'id': 'P073', 'name': '金枪鱼泡菜炒饭', 'category': '主食/炒饭', 'price': 25, 'stock': 100, 'description': '韩式风味，微辣开胃，韩剧同款'},
    {'id': 'P074', 'name': '黑松露牛肉炒饭', 'category': '主食/炒饭', 'price': 48, 'stock': 100, 'description': '西餐厅品质，浓郁黑松露香，安格斯牛肉粒'},
    {'id': 'P075', 'name': '正宗广式干炒牛河', 'category': '主食/炒饭', 'price': 32, 'stock': 100, 'description': '大厨现炒，牛肉滑嫩，锅气十足，不粘不散'},
    {'id': 'P076', 'name': '菠萝海鲜炒饭', 'category': '主食/炒饭', 'price': 38, 'stock': 100, 'description': '泰式风味，新鲜菠萝半个打底，腰果提香'},
    {'id': 'P077', 'name': '台湾卤肉饭', 'category': '主食/炒饭', 'price': 29, 'stock': 100, 'description': '五花肉肥而不腻，配灵魂卤蛋和酸菜，米饭杀手'},
    {'id': 'P078', 'name': '日式鳗鱼饭', 'category': '主食/炒饭', 'price': 68, 'stock': 100, 'description': '蒲烧鳗鱼全段，特调酱汁，软糯米饭'},
    {'id': 'P079', 'name': '川味麻婆豆腐盖饭', 'category': '主食/炒饭', 'price': 22, 'stock': 100, 'description': '麻辣烫香酥，下饭神菜，分量超大'},
    {'id': 'P080', 'name': '印尼炒饭 (Nasi Goreng)', 'category': '主食/炒饭', 'price': 32, 'stock': 100, 'description': '甜黑酱油风味，配沙嗲肉串和虾片'},
    {'id': 'P081', 'name': '福建海鲜焖饭', 'category': '主食/炒饭', 'price': 45, 'stock': 100, 'description': '干贝、干虾仁、鱿鱼、香菇焖煮，鲜到掉眉毛'},
    {'id': 'P082', 'name': '新疆羊肉手抓饭', 'category': '主食/炒饭', 'price': 42, 'stock': 100, 'description': '胡萝卜与羊排的完美结合，米粒吸满油脂'},
    {'id': 'P083', 'name': '老北京炸酱面', 'category': '主食/炒饭', 'price': 26, 'stock': 100, 'description': '七分瘦三分肥肉丁，黄酱干黄酱秘制，菜码丰富'},
    {'id': 'P084', 'name': '重庆小面', 'category': '主食/炒饭', 'price': 18, 'stock': 100, 'description': '麻辣红油，豌杂软烂，街头风味'},
    {'id': 'P085', 'name': '武汉热干面', 'category': '主食/炒饭', 'price': 15, 'stock': 100, 'description': '浓郁芝麻酱，搭配酸豆角和萝卜丁，过早必备'},
    {'id': 'P086', 'name': '广式腊味萝卜糕', 'category': '主食/炒饭', 'price': 28, 'stock': 100, 'description': '500g装，煎至两面金黄，入口即化，香气四溢'},
    {'id': 'P087', 'name': '韩式石锅拌饭', 'category': '主食/炒饭', 'price': 30, 'stock': 100, 'description': '多彩蔬菜搭配灵魂辣酱，底部焦香锅巴'},
    {'id': 'P088', 'name': '台式三杯鸡便当', 'category': '主食/炒饭', 'price': 35, 'stock': 100, 'description': '罗勒叶提香，鸡腿肉嫩滑，经典台式便当'},
    {'id': 'P089', 'name': '咖喱猪排饭', 'category': '主食/炒饭', 'price': 38, 'stock': 100, 'description': '日式浓厚咖喱，炸猪排外酥里嫩，米饭好伴侣'},
    {'id': 'P090', 'name': '咸蛋黄大虾炒饭', 'category': '主食/炒饭', 'price': 36, 'stock': 100, 'description': '咸蛋黄裹满米粒和虾仁，金黄诱人，色香味俱全'},
    {'id': 'P091', 'name': '三只松鼠坚果大礼包', 'category': '零食小吃', 'price': 88, 'stock': 100, 'description': '夏威夷果、碧根果等8袋装，追剧必备'},
    {'id': 'P092', 'name': '卫龙辣条组合包', 'category': '零食小吃', 'price': 29, 'stock': 100, 'description': '大面筋、亲嘴烧，儿时味道，辣得过瘾'},
    {'id': 'P093', 'name': '良品铺子鸭脖', 'category': '零食小吃', 'price': 35, 'stock': 100, 'description': '麻辣/甜辣可选，独立包装，肉质紧实'},
    {'id': 'P094', 'name': '乐事薯片家庭装', 'category': '零食小吃', 'price': 25, 'stock': 100, 'description': '5连包，黄瓜、原味、烧烤经典口味组合'},
    {'id': 'P095', 'name': '大白兔奶糖', 'category': '零食小吃', 'price': 19, 'stock': 100, 'description': '500g袋装，经典奶香，国民记忆'},
    {'id': 'P096', 'name': '周黑鸭锁鲜装', 'category': '零食小吃', 'price': 45, 'stock': 100, 'description': '鸭锁骨+鸭翅，甜辣麻香，冷链配送'},
    {'id': 'P097', 'name': '奥利奥夹心饼干', 'category': '零食小吃', 'price': 22, 'stock': 100, 'description': '扭一扭舔一舔泡一泡，多种口味混合装'},
    {'id': 'P098', 'name': '百草味芒果干', 'category': '零食小吃', 'price': 29, 'stock': 100, 'description': '厚切果肉，酸甜软糯，不塞牙'},
    {'id': 'P099', 'name': '星巴克星冰乐咖啡饮料', 'category': '零食小吃', 'price': 59, 'stock': 100, 'description': '281ml*6瓶，摩卡/咖啡味，冰镇更佳'},
    {'id': 'P100', 'name': '旺旺仙贝雪饼大礼包', 'category': '零食小吃', 'price': 39, 'stock': 100, 'description': '酥脆可口，过年送礼或日常解馋'},
    {'id': 'P101', 'name': '新疆和田大红枣', 'category': '零食小吃', 'price': 45, 'stock': 100, 'description': '500g*2袋，免洗六星级大枣，核小肉厚'},
    {'id': 'P102', 'name': '内蒙古风干牛肉干', 'category': '零食小吃', 'price': 99, 'stock': 100, 'description': '500g，七成干，越嚼越香，高蛋白低脂肪'},
    {'id': 'P103', 'name': '海底捞自热火锅', 'category': '零食小吃', 'price': 39, 'stock': 100, 'description': '脆爽牛肚/番茄牛腩，随时随地吃火锅'},
    {'id': 'P104', 'name': '螺霸王柳州螺蛳粉', 'category': '零食小吃', 'price': 49, 'stock': 100, 'description': '3袋装，加臭加辣，腐竹花生料超足'},
    {'id': 'P105', 'name': '轩妈蛋黄酥', 'category': '零食小吃', 'price': 45, 'stock': 100, 'description': '一盒6枚，雪媚娘红豆沙咸蛋黄，多层口感'},
    {'id': 'P106', 'name': '徐福记沙琪玛', 'category': '零食小吃', 'price': 25, 'stock': 100, 'description': '松软香甜，独立小包装，早餐下午茶'},
    {'id': 'P107', 'name': '黄飞红麻辣花生', 'category': '零食小吃', 'price': 22, 'stock': 100, 'description': '花椒辣椒与花生的碰撞，下酒好菜'},
    {'id': 'P108', 'name': '洽洽香瓜子', 'category': '零食小吃', 'price': 18, 'stock': 100, 'description': '500g大包装，经典五香味，嗑不停'},
    {'id': 'P109', 'name': '白色恋人巧克力夹心饼干', 'category': '零食小吃', 'price': 89, 'stock': 100, 'description': '日本进口18枚装，网红伴手礼，香浓丝滑'},
    {'id': 'P110', 'name': '溜溜梅全家桶', 'category': '零食小吃', 'price': 35, 'stock': 100, 'description': '多种口味话梅组合，酸甜提神'},
    {'id': 'P111', 'name': '云南高原高山菠菜', 'category': '生鲜蔬菜', 'price': 15, 'stock': 100, 'description': '1000g，鲜嫩少涩味，适合凉拌炒菜'},
    {'id': 'P112', 'name': '山东寿光普罗旺斯西红柿', 'category': '生鲜蔬菜', 'price': 25, 'stock': 100, 'description': '3斤装，沙瓤多汁，可直接当水果吃'},
    {'id': 'P113', 'name': '东北铁棍山药', 'category': '生鲜蔬菜', 'price': 35, 'stock': 100, 'description': '5斤礼盒装，粉糯香甜，煲汤清蒸皆宜'},
    {'id': 'P114', 'name': '大荔沙苑红薯', 'category': '生鲜蔬菜', 'price': 22, 'stock': 100, 'description': '5斤装，粉甜无丝，烤地瓜绝佳选择'},
    {'id': 'P115', 'name': '有机鲜香菇', 'category': '生鲜蔬菜', 'price': 18, 'stock': 100, 'description': '500g，肉质肥厚，鲜香浓郁，炖鸡佳品'},
    {'id': 'P116', 'name': '净菜土豆丝', 'category': '生鲜蔬菜', 'price': 9, 'stock': 100, 'description': '300g免洗免切，清水浸泡防氧化，直接下锅'},
    {'id': 'P117', 'name': '海南桥头地瓜', 'category': '生鲜蔬菜', 'price': 28, 'stock': 100, 'description': '5斤装，皮爆瓤红，香甜可口'},
    {'id': 'P118', 'name': '白玉水谷水果萝卜', 'category': '生鲜蔬菜', 'price': 19, 'stock': 100, 'description': '5斤装，清脆爽口，微甜微辣，凉拌佳品'},
    {'id': 'P119', 'name': '四川大凉山丑苹果', 'category': '生鲜蔬菜', 'price': 39, 'stock': 100, 'description': '5斤装，冰糖心，其貌不扬但脆甜入心'},
    {'id': 'P120', 'name': '云南保山甜脆玉米', 'category': '生鲜蔬菜', 'price': 29, 'stock': 100, 'description': '8根装，可生食的水果玉米，爆汁清甜'},
    {'id': 'P121', 'name': '本地现摘空心菜', 'category': '生鲜蔬菜', 'price': 12, 'stock': 100, 'description': '500g，鲜嫩翠绿，蒜蓉爆炒最佳'},
    {'id': 'P122', 'name': '金乡大蒜', 'category': '生鲜蔬菜', 'price': 15, 'stock': 100, 'description': '3斤网兜装，蒜香浓郁，厨房调味必备'},
    {'id': 'P123', 'name': '山东胶州大白菜', 'category': '生鲜蔬菜', 'price': 18, 'stock': 100, 'description': '整颗约5斤，包心紧实，炖豆腐/做辣白菜'},
    {'id': 'P124', 'name': '云南七彩花生', 'category': '生鲜蔬菜', 'price': 25, 'stock': 100, 'description': '2斤生花生，富含花青素，水煮最营养'},
    {'id': 'P125', 'name': '甘肃民勤黄河蜜瓜', 'category': '生鲜蔬菜', 'price': 35, 'stock': 100, 'description': '2个装，网纹清晰，瓜肉如蜜'},
    {'id': 'P126', 'name': '水洗鲜海带苗', 'category': '生鲜蔬菜', 'price': 19, 'stock': 100, 'description': '500g，超级嫩滑，只需焯水1分钟'},
    {'id': 'P127', 'name': '有机胡萝卜', 'category': '生鲜蔬菜', 'price': 16, 'stock': 100, 'description': '3斤装，带泥保鲜，汁水丰富适合榨汁'},
    {'id': 'P128', 'name': '崇明本地小菠菜', 'category': '生鲜蔬菜', 'price': 18, 'stock': 100, 'description': '红头小菠菜500g，超级嫩，无农药残留'},
    {'id': 'P129', 'name': '东北秋林特产黑木耳', 'category': '生鲜蔬菜', 'price': 49, 'stock': 100, 'description': '250g干货，泡发率高，无根免洗肉厚'},
    {'id': 'P130', 'name': '泰国进口香水椰青', 'category': '生鲜蔬菜', 'price': 69, 'stock': 100, 'description': '6个装，开壳器+吸管，椰汁清甜，椰肉Q弹'},
]

# ========== 订单库 ============
ORDERS = [
    {"id": "ORD001", "user": "张三", "product_id": "P001", "product_name": "iPhone 15 Pro Max",
     "quantity": 1, "total": 9999, "status": "已完成", "created_at": "2024-03-01 10:30:00",
     "payment_method": "支付宝", "shipping_address": "北京市朝阳区xxx"},
    {"id": "ORD002", "user": "李四", "product_id": "P004", "product_name": "Sony WH-1000XM5",
     "quantity": 2, "total": 5398, "status": "配送中", "created_at": "2024-03-05 14:20:00",
     "payment_method": "微信支付", "shipping_address": "上海市浦东新区xxx",
     "tracking_number": "SF1234567890"},
    {"id": "ORD003", "user": "王五", "product_id": "P007", "product_name": "Nike Air Max 270",
     "quantity": 1, "total": 1099, "status": "已退款", "created_at": "2024-02-20 09:15:00",
     "payment_method": "信用卡", "refund_reason": "尺码不合适", "refund_time": "2024-02-25 16:00:00"},
    {"id": "ORD004", "user": "赵六", "product_id": "P005", "product_name": "MacBook Pro 14",
     "quantity": 1, "total": 14999, "status": "待发货", "created_at": "2024-03-10 11:00:00",
     "payment_method": "Apple Pay", "shipping_address": "深圳市南山区xxx"},
    {"id": "ORD005", "user": "钱七", "product_id": "P009", "product_name": "优衣库 极暖内衣套装",
     "quantity": 3, "total": 597, "status": "已完成", "created_at": "2024-01-15 08:45:00",
     "payment_method": "微信支付", "shipping_address": "杭州市西湖区xxx"},
]

# ========== 知识库 ==========
KNOWLEDGE_BASE = [
    {
        "topic": "退换货政策",
        "keywords": ["退货", "换货", "退款", "退换", "7天", "无理由"],
        "content": """【退换货政策】
1. 自签收之日起 7 天内可申请无理由退换货（部分特殊商品除外）
2. 退货商品需保持原包装完好，不影响二次销售
3. 退款将在收到退货后 3-5 个工作日原路退回
4. 已使用/拆封的电子产品仅支持质量问题退换
5. 定制商品、贴身衣物（内衣类）不支持无理由退换"""
    },
    {
        "topic": "运费说明",
        "keywords": ["运费", "包邮", "快递", "配送", "物流"],
        "content": """【运费说明】
1. 订单满 99 元包邮（偏远地区除外）
2. 未满 99 元收取 10 元运费
3. 偏远地区（新疆、西藏、青海）加收 15 元
4. 大件商品（家电类）使用专线物流，运费单独计算
5. 退货运费：质量问题由商家承担，其他原因由买家承担"""
    },
    {
        "topic": "会员权益",
        "keywords": ["会员", "VIP", "积分", "等级", "折扣", "优惠"],
        "content": """【会员权益】
1. 普通会员：注册即享，消费积分 1:1
2. 银卡会员：年消费满 2000 元，享 95 折
3. 金卡会员：年消费满 5000 元，享 9 折 + 生日礼券
4. 钻石会员：年消费满 20000 元，享 85 折 + 专属客服 + 免费退换货运费
5. 积分可在积分商城兑换商品或优惠券"""
    },
    {
        "topic": "支付方式",
        "keywords": ["支付", "付款", "支付宝", "微信", "信用卡", "花呗", "分期"],
        "content": """【支付方式】
1. 支持：支付宝、微信支付、银联云闪付、Apple Pay
2. 支持信用卡分期：3期免息、6期/12期低息
3. 支持花呗分期
4. 订单超过 30 分钟未付款将自动取消
5. 退款原路返回，分期订单退款会取消分期"""
    },
    {
        "topic": "售后服务",
        "keywords": ["售后", "保修", "维修", "质量", "损坏", "投诉"],
        "content": """【售后服务】
1. 电子产品享受 1 年官方保修（人为损坏除外）
2. 服饰类 30 天内质量问题免费换新
3. 人工客服工作时间：9:00-21:00（节假日正常服务）
4. 投诉渠道：在线客服 > 电话 400-xxx-xxxx > 邮件 service@example.com
5. 投诉处理时限：24 小时内首次回复"""
    },
    {
        "topic": "账户安全",
        "keywords": ["账户", "密码", "登录", "绑定", "手机号", "安全", "冻结", "注销"],
        "content": """【账户安全】
1. 登录密码需包含字母+数字，长度不少于 8 位
2. 支持手机验证码登录、微信/支付宝第三方登录
3. 忘记密码可通过绑定手机号重置
4. 账户异常（异地登录等）将自动冻结，需验证身份后解冻
5. 更换绑定手机号需同时验证新旧手机号
6. 账户注销需确保无未完成订单及余额清零，注销后数据不可恢复"""
    },
    {
        "topic": "优惠券与促销活动",
        "keywords": ["优惠券", "折扣", "促销", "活动", "满减", "红包", "秒杀", "拼团"],
        "content": """【优惠券与促销活动】
1. 优惠券可在“我的 > 优惠券”中查看，需在有效期内使用
2. 每笔订单仅限使用一张优惠券（积分抵扣除外）
3. 满减优惠与优惠券可叠加使用
4. 秒杀商品限购 1 件/人，不支持与其他优惠叠加
5. 拼团活动需在 24 小时内凑满人数，否则自动退款
6. 新用户专享券仅限注册后 7 天内使用"""
    },
    {
        "topic": "配送时效",
        "keywords": ["配送", "发货", "到货", "时效", "自提", "预计", "时间"],
        "content": """【配送时效】
1. 现货商品：付款后 24 小时内发货（节假日顺延）
2. 预售商品：按商品页标注的预计发货时间
3. 同城配送：下单后 2-4 小时送达（限部分城市）
4. 普通快递：发货后 2-5 天到达
5. 自提服务：部分商品支持门店自提，下单时选择自提门店
6. 可在“我的订单”中查看物流追踪信息"""
    },
    {
        "topic": "发票开具",
        "keywords": ["发票", "开票", "电子发票", "增值税", "抬头"],
        "content": """【发票开具】
1. 支持电子普通发票和电子增值税专用发票
2. 电子发票在订单完成后自动发送至注册邮箱
3. 如需修改发票抬头，请在下单时填写或联系客服
4. 增值税专用发票需提供公司名称、纳税人识别号等信息
5. 发票金额为实际支付金额（扣除优惠部分）
6. 退货退款后对应发票自动作废"""
    },
    {
        "topic": "商品真伪与质量保证",
        "keywords": ["正品", "假货", "真伪", "鉴别", "质量", "授权", "防伪"],
        "content": """【商品真伪与质量保证】
1. 所有商品均为品牌授权正品，支持官方验证
2. 每件商品附带防伪溯源码，可扫码查验真伪
3. 如收到疑似假货，可拍照举报，48 小时内核实处理
4. 经核实确为假货，承诺假一赔十
5. 入驻商家均经过严格资质审核和定期抽检"""
    },
    {
        "topic": "安装与调试服务",
        "keywords": ["安装", "调试", "上门", "师傅", "预约", "家电安装"],
        "content": """【安装与调试服务】
1. 大型家电（冰箱、洗衣机、空调等）提供免费送货上门及安装
2. 安装预约：订单完成后在 APP 内选择“预约安装”，选择上门时间
3. 工程师上门时间：9:00-18:00（可选周末）
4. 安装不含额外材料费（如空调铜管加长等另计）
5. 小型家电与数码产品不提供上门安装，可拨打客服获取远程指导"""
    },
    {
        "topic": "隐私保护政策",
        "keywords": ["隐私", "个人信息", "数据", "信息安全", "授权", "Cookie"],
        "content": """【隐私保护政策】
1. 仅收集订单相关的必要个人信息（姓名、地址、手机号）
2. 未经用户同意，不会向第三方分享个人信息
3. 支付信息采用银行级加密传输，不存储完整银行卡号
4. 用户可在“设置 > 隐私”中管理授权和数据下载
5. 收到营销信息后可随时取消订阅
6. 如需删除个人数据，可提交数据删除请求，15 个工作日内处理"""
    }
]


def search_products(query: str, **kwargs) -> list:
    """搜索商品（按名称或类别模糊匹配，兼容 LLM 传入的额外参数如 category）"""
    # LLM 可能传入 category 等额外参数，合并到搜索关键词中
    if 'category' in kwargs and kwargs['category'] != query:
        query = f"{query} {kwargs['category']}"
    query_lower = query.lower()
    results = []
    for p in PRODUCTS:
        if (query_lower in p["name"].lower() or 
            query_lower in p["category"].lower() or
            query_lower in p["description"].lower()):
            results.append(p)
    return results if results else [{"message": f"未找到与 '{query}' 相关的商品"}]


def get_product_detail(product_id: str) -> dict:
    """获取商品详情"""
    for p in PRODUCTS:
        if p["id"] == product_id.upper():
            return p
    return {"error": f"商品 {product_id} 不存在"}


def get_order_info(order_id: str) -> dict:
    """查询订单信息"""
    for o in ORDERS:
        if o["id"] == order_id.upper():
            return o
    return {"error": f"订单 {order_id} 不存在"}


def apply_refund(order_id: str, reason: str) -> dict:
    """申请退款（模拟）"""
    for o in ORDERS:
        if o["id"] == order_id.upper():
            if o["status"] == "已退款":
                return {"success": False, "message": f"订单 {order_id} 已经退过款了"}
            if o["status"] == "配送中":
                return {"success": False, "message": f"订单 {order_id} 正在配送中，请先签收后再申请退款"}
            # 模拟退款成功
            return {
                "success": True,
                "message": f"退款申请已提交",
                "refund_info": {
                    "order_id": order_id.upper(),
                    "product": o["product_name"],
                    "refund_amount": o["total"],
                    "reason": reason,
                    "estimated_refund_time": "3-5 个工作日"
                }
            }
    return {"success": False, "message": f"订单 {order_id} 不存在"}


def query_knowledge(question: str) -> str:
    """查询知识库（关键词匹配）"""
    question_lower = question.lower()
    matched = []
    for item in KNOWLEDGE_BASE:
        for keyword in item["keywords"]:
            if keyword in question_lower:
                matched.append(item)
                break
    
    if matched:
        return "\n\n---\n\n".join([m["content"] for m in matched])
    return "抱歉，知识库中没有找到相关信息。请联系人工客服获取帮助。"
