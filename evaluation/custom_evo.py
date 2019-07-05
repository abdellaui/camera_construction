#!/usr/bin/env python

from __future__ import print_function
from evo.core import trajectory, sync, metrics
from evo.tools import file_interface
from evo.tools import plot
from evo.tools.settings import SETTINGS
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-r","--ref", required=True, help="path to dataset.txt")
parser.add_argument("-e","--estimate", type=str, default="", help="prefix for the stored filename")
opt = parser.parse_args()

figuresize=(8, 4)

print("loading required evo modules")

print("loading trajectories")
traj_ref = file_interface.read_tum_trajectory_file(opt.ref)
traj_est = file_interface.read_tum_trajectory_file(opt.estimate)

print("registering and aligning trajectories")
#traj_ref, traj_est = sync.associate_trajectories(traj_ref, traj_est)
#traj_est = trajectory.align_trajectory(traj_est, traj_ref, correct_scale=False)

print("calculating APE")
data = (traj_ref, traj_est)
ape_metric = metrics.APE(metrics.PoseRelation.translation_part)
ape_metric.process_data(data)
ape_statistics = ape_metric.get_all_statistics()
print("mean:", ape_statistics["mean"])

print("loading plot modules")

print("plotting")
plot_collection = plot.PlotCollection("Example")
# metric values
fig_1 = plt.figure(figsize=figuresize)
plot.error_array(fig_1, ape_metric.error, statistics=ape_statistics,
                 name="APE", title=str(ape_metric))
plot_collection.add_figure("raw", fig_1)



# trajectory colormapped with error
fig_2 = plt.figure(figsize=figuresize)
plot_mode = plot.PlotMode.xy
ax = plot.prepare_axis(fig_2, plot_mode)
plot.traj(ax, plot_mode, traj_ref, '.', 'red', 'reference')
plot.traj_colormap(
    ax, traj_est, ape_metric.error, plot_mode, min_map=0,
    max_map=ape_statistics["max"])

plot_collection.add_figure("traj (error)", fig_2)



# xyz, rpy
fig_xyz, axarr_xyz = plt.subplots(3, sharex="col", figsize=figuresize)
plot.traj_xyz(
    axarr_xyz, traj_ref, style=SETTINGS.plot_reference_linestyle,
                color=SETTINGS.plot_reference_color, label='ground truth',
                alpha=SETTINGS.plot_reference_alpha)

plot.traj_xyz(
    axarr_xyz, traj_est, style='-',
                color='blue', label='estimated',
                alpha=1)
plot_collection.add_figure("xyz_view", fig_xyz)

# rpy
fig_rpy, axarr_rpy = plt.subplots(3, sharex="col", figsize=figuresize)
plot.traj_rpy(
    axarr_rpy, traj_ref, style=SETTINGS.plot_reference_linestyle,
                color=SETTINGS.plot_reference_color, label='ground truth',
                alpha=SETTINGS.plot_reference_alpha)       

plot.traj_rpy(
    axarr_rpy, traj_est, style='-',
                color='blue', label='estimated',
                alpha=1)

plot_collection.add_figure("xyz_view", fig_xyz)  
plot_collection.add_figure("rpy_view", fig_rpy)

        
plot_collection.show()