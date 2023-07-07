import os

paths = [
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/scale_render/v001/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/main_help02_plate01_/v001/2104_1138_exr/621_025_sq_0150_pnt_main_help02_plate01__v001.1084.exr',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/sr_hair_wip_2/v001/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/sl_strokes/v001/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/sl_strokes_without_hair/v001/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/correction_strokes/v002/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/Head/v002/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/1065/v001/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/bg_1210/v003/2500_1500_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/main_help01/v008/2104_1138_exr/',
    '/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img/denoise/v001/2104_1138_exr/'
]

new_dir = '/digi/prod/Projects/FEATURE/VODD_621/0_DELIVERABLES/DLV/DLV_VODD_621_20190731A/LEG_20190715A/VODD_Batch01_prep_20190715/IC_025_sq_0150_plt_02_v1_prep_v1/dependencies'

for path in paths:
    if os.path.isdir(path):
        new_path = path.replace('/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img', new_dir)

        if not os.path.exists(new_path):
            os.makedirs(new_path)

        for f in os.listdir(path):
            src = os.path.join(path, f)
            dst = os.path.join(new_path, f)

            if os.path.isfile(src):
                os.link(src, dst)

            print(dst)

    elif os.path.isfile(path):
        file_dir, file_name = os.path.split(path)

        new_path = file_dir.replace('/digi/prod/Projects/FEATURE/VODD_621/shots/621_025_sq_0150/pnt/img', new_dir)

        if not os.path.exists(new_path):
            os.makedirs(new_path)

        dst = os.path.join(new_path, file_name)
        os.link(path, dst)

        print(dst)
