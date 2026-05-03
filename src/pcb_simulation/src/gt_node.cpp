#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/imu.hpp>

#include <gz/transport/Node.hh>
#include <gz/msgs/pose_v.pb.h>

class GTNode : public rclcpp::Node
{
public:
  GTNode() : Node("gt_node", rclcpp::NodeOptions()
  .parameter_overrides({rclcpp::Parameter("use_sim_time", true)}))
  {
    pub_odom_ = this->create_publisher<nav_msgs::msg::Odometry>(
      "/ground_truth/odom", 10);

    pub_imu_ = this->create_publisher<sensor_msgs::msg::Imu>(
      "/imu/fixed", 10);

    sub_imu_ = this->create_subscription<sensor_msgs::msg::Imu>(
      "/imu",
      10,
      std::bind(&GTNode::imuCb, this, std::placeholders::_1));

    node_.Subscribe(
      "/world/simple_world/pose/info",
      &GTNode::cb,
      this);
  }

private:

  // =========================
  // GAZEBO GROUND TRUTH ODOM
  // =========================
  void cb(const gz::msgs::Pose_V & msg)
  {
    for (int i = 0; i < msg.pose_size(); i++)
    {
      const auto & p = msg.pose(i);

      if (p.name() == "simple_robot")
      {
        nav_msgs::msg::Odometry odom;

        odom.header.stamp = this->get_clock()->now();
        odom.header.frame_id = "odom";
        odom.child_frame_id = "base_footprint";

        odom.pose.pose.position.x = p.position().x();
        odom.pose.pose.position.y = p.position().y();
        odom.pose.pose.position.z = p.position().z();

        odom.pose.pose.orientation.x = p.orientation().x();
        odom.pose.pose.orientation.y = p.orientation().y();
        odom.pose.pose.orientation.z = p.orientation().z();
        odom.pose.pose.orientation.w = p.orientation().w();

        pub_odom_->publish(odom);
      }
    }
  }

  // =========================
  // IMU FIX (covariance inject)
  // =========================
  void imuCb(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    sensor_msgs::msg::Imu out = *msg;

    // Orientation covariance (uniquement yaw important en 2D)
    out.orientation_covariance = {
        1000.0, 0.0, 0.0,     // roll - ignoré en 2D
        0.0, 1000.0, 0.0,     // pitch - ignoré en 2D
        0.0, 0.0, 0.005       // yaw - PRÉCIS (0.005 rad² ≈ 4°)
    };

    // Angular velocity covariance
    out.angular_velocity_covariance = {
        1000.0, 0.0, 0.0,     // vroll - ignoré
        0.0, 1000.0, 0.0,     // vpitch - ignoré
        0.0, 0.0, 0.01        // vyaw - utilisé
    };

    // Linear acceleration covariance
    out.linear_acceleration_covariance = {
        0.05, 0.0, 0.0,       // ax - RÉDUIT (meilleure qualité)
        0.0, 0.05, 0.0,       // ay - RÉDUIT
        0.0, 0.0, 0.05      // az - IGNORÉ en 2D
    };

    pub_imu_->publish(out);
  }

  // =========================
  // MEMBERS
  // =========================
  gz::transport::Node node_;

  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr pub_odom_;
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr pub_imu_;
  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr sub_imu_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<GTNode>());
  rclcpp::shutdown();
}