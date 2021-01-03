import numpy as np

def calc_TFL_dist(prev_container, curr_container, focal, pp):
    norm_prev_pts, norm_curr_pts, R, foe, tZ = prepare_3D_data(prev_container, curr_container, focal, pp)
    if(abs(tZ) < 10e-6):
        print('tz = ', tZ)
    elif (norm_prev_pts.size == 0):
        print('no prev points')
    elif (norm_curr_pts.size == 0):
        print('no curr points')
    else:
        curr_container.corresponding_ind, curr_container.traffic_lights_3d_location, curr_container.valid = calc_3D_data(norm_prev_pts, norm_curr_pts, R, foe, tZ)
    return curr_container

def prepare_3D_data(prev_container, curr_container, focal, pp):
    print("p", prev_container.traffic_light)
    print("c", curr_container.traffic_light)
    norm_prev_pts = normalize(prev_container.traffic_light, focal, pp)
    norm_curr_pts = normalize(curr_container.traffic_light, focal, pp)
    R, foe, tZ = decompose(np.array(curr_container.EM))
    return norm_prev_pts, norm_curr_pts, R, foe, tZ

def calc_3D_data(norm_prev_pts, norm_curr_pts, R, foe, tZ):
    norm_rot_pts = rotate(norm_prev_pts, R)
    pts_3D = []
    corresponding_ind = []
    validVec = []
    for p_curr in norm_curr_pts:
        corresponding_p_ind, corresponding_p_rot = find_corresponding_points(p_curr, norm_rot_pts, foe)
        Z = calc_dist(p_curr, corresponding_p_rot, foe, tZ)
        print('p_curr', p_curr)
        print('corresponding_p_rot', corresponding_p_rot)
        print('foe', foe)
        print('tZ', tZ)
        valid = (Z > 0)
        if not valid:
            Z = 0
        validVec.append(valid)
        P = Z * np.array([p_curr[0], p_curr[1], 1])
        pts_3D.append((P[0], P[1], P[2]))
        corresponding_ind.append(corresponding_p_ind)
    return corresponding_ind, np.array(pts_3D), validVec

def normalize(pts, focal, pp):
    # transform pixels into normalized pixels using the focal length and principle point
    pts_ = [(point - pp) / focal for point in pts]
    return np.array(pts_)

def unnormalize(pts, focal, pp):
    # transform normalized pixels into pixels using the focal length and principle point
    pts_ = [(point * focal ) +  pp for point in pts]
    return np.array(pts_)

def decompose(EM):
    # extract R, foe and tZ from the Ego Motion
    R = EM[:3, :3]
    tX = EM[0, 3]
    tY = EM[1, 3]
    tZ = EM[2, 3]
    foe = np.array([tX / tZ, tY / tZ])
    return R, foe, tZ

def rotate(pts, R):
    # rotate the points - pts using R
    res = []
    for point in pts:
        pts3d = np.array([point[0], point[1], 1])
        [a, b, c] = np.dot(R, pts3d)
        res.append(np.array([a/c , b/c]))
    return res

def find_corresponding_points(p, norm_pts_rot, foe):
    # compute the epipolar line between p and foe
    # run over all norm_pts_rot and find the one closest to the epipolar line
    # return the closest point and its index
    m = (foe[1] - p[1]) / ((foe[0] - p[0]))
    n = (p[1] * foe[0] - foe[1] * p[0]) / (foe[0] - p[0])
    min_ = None
    index_ = -1
    for i, point in enumerate(norm_pts_rot):
        tmp = abs( ((m * point[0] + n)- point[1]) / pow((pow(m, 2) + 1), 0.5))
        if index_ == -1 or tmp < min_:
            min_ = tmp
            index_ = i
    return index_, norm_pts_rot[index_]
        

def calc_dist(p_curr, p_rot, foe, tZ):
    # calculate the distance of p_curr using x_curr, x_rot, foe_x and tZ
    # calculate the distance of p_curr using y_curr, y_rot, foe_y and tZ
    # combine the two estimations and return estimated Z
    z_per_x = (tZ * (foe[0] - p_rot[0])) / (p_curr[0] - p_rot[0])
    z_per_y = (tZ * (foe[1] - p_rot[1])) / (p_curr[1] - p_rot[1])
    print('z_per_x', z_per_x)
    print('z_per_y', z_per_y)
    return abs(z_per_x + z_per_y) / 2