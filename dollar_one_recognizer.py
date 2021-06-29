import sys
import numpy as np
from dollar_one_utils import calc_dist_at_best_angle, calc_path_length, calc_euclidean_distance, get_bounding_box, \
    calc_centroid, rotate_by


class DollarOneRecognizer:

    def __init__(self):
        pass

    def resample_points(self, original_points: list[tuple[int, int]], num_resampled_points=64):
        """
        The original input points must be in the form of [(x, y), ...].
        """

        if len(original_points) <= 1:
            sys.stderr.write("Too few input points were given! At least two are needed!")
            return

        step_size = calc_path_length(original_points) / (num_resampled_points - 1)
        current_distance = 0
        new_points = [original_points[0]]  # create a new array and init with the first point

        for i in range(1, len(original_points)):
            last_point = original_points[i-1]
            current_point = original_points[i]
            d = calc_euclidean_distance(last_point, current_point)

            if (current_distance + d) >= step_size:
                # if the distance to the next point is greater than the step size, we have to calculated
                # a new resampled point
                px = last_point[0] + ((step_size - current_distance) / d) * (current_point[0] - last_point[0])
                py = last_point[1] + ((step_size - current_distance) / d) * (current_point[1] - last_point[1])
                resampled_point = (px, py)
                new_points.append(resampled_point)

                # insert the new resampled point at the next position in the original list, so it will be the next
                # current_point!
                original_points.insert(i, resampled_point)
            else:
                # step size was not reached, just go further
                current_distance += d

        return new_points

    def rotate_to_zero(self, points):
        centroid = calc_centroid(points)
        first_point_x = points[0][0]
        first_point_y = points[0][1]
        rotate_angle = np.arctan2(centroid[1] - first_point_y, centroid[0] - first_point_x)  # TODO * 180 / np.pi ?

        rotated_points = rotate_by(points=points, angle=-rotate_angle)
        return rotated_points

    def scale_to_square(self, points, square_size=100):
        bbox = get_bounding_box(points)
        # bounding box in the form: [(min_x, min_y), (max_x, max_y)]
        bbox_width = bbox[1][0] - bbox[0][0]
        bbox_height = bbox[1][1] - bbox[0][1]

        new_points = []
        for point in points:
            p_x = point[0] * (square_size / bbox_width)
            p_y = point[1] * (square_size / bbox_height)
            scaled_point = [p_x, p_y]
            new_points.append(scaled_point)
        return new_points

    def translate_to_origin(self, points):
        centroid = calc_centroid(points)
        new_points = []
        for point in points:
            p_x = point[0] - centroid[0]
            p_y = point[1] - centroid[1]
            new_points.append([p_x, p_y])
        return new_points

    def recognize(self, points, templates, square_size=100):
        if len(templates) < 1:
            return

        T_new = None
        b = np.inf
        for template in templates:
            # angle values based on the original paper:
            # TODO convert degrees to radians first?
            # degree_to_radians(45)
            dist = calc_dist_at_best_angle(points, template, -45, 45, 2)
            if dist < b:
                b = dist
                T_new = template

        if T_new is None:
            return
        score = 1 - b / 0.5 * np.sqrt(square_size**2 + square_size**2)
        return np.dot(T_new, score)

    def normalize(self,points):
        # use all the processing functions from above to transform our set of points into the desired shape
        resampled_points = self.resample_points(points)
        point_array = np.array(resampled_points)  # convert to numpy array for further calculations
        rotated_points = self.rotate_to_zero(point_array)
        scaled_points = self.scale_to_square(rotated_points, square_size=100)
        translated_points = self.translate_to_origin(scaled_points)
        return translated_points
