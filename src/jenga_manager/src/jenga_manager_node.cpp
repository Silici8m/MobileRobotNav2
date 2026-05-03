#include <memory>
#include <vector>
#include <string>
#include <set>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_lifecycle/lifecycle_node.hpp"
#include "nav2_virtual_layer/srv/add_polygon.hpp"
#include "nav2_virtual_layer/srv/remove_shape.hpp"
#include "std_srvs/srv/trigger.hpp"
#include "geometry_msgs/msg/point.hpp"

#include "jenga_manager/jenga.hpp"
#include "jenga_manager/group.hpp"
#include "jenga_manager/jenga_state.hpp"

using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class JengaManager : public rclcpp_lifecycle::LifecycleNode {
public:

    JengaManager() : LifecycleNode(
        "jenga_manager",
        rclcpp::NodeOptions()
            .allow_undeclared_parameters(true)
            .automatically_declare_parameters_from_overrides(true)
    ) {
        world_ = std::make_unique<WorldState>();
    }


    // Configuration
    CallbackReturn on_configure(const rclcpp_lifecycle::State &) override {
        RCLCPP_INFO(get_logger(), "Configuring Jenga Manager...");
        
        client_add_global_ = this->create_client<nav2_virtual_layer::srv::AddPolygon>(
            "/global_costmap/virtual_layer/add_polygon");

        client_remove_global_ = this->create_client<nav2_virtual_layer::srv::RemoveShape>(
        "/global_costmap/virtual_layer/remove_shape");

        client_clear_all_global_ = this->create_client<std_srvs::srv::Trigger>(
        "/global_costmap/virtual_layer/clear_all");

        client_add_local_ = this->create_client<nav2_virtual_layer::srv::AddPolygon>(
        "/local_costmap/virtual_layer/add_polygon");

        client_remove_local_ = this->create_client<nav2_virtual_layer::srv::RemoveShape>(
        "/local_costmap/virtual_layer/remove_shape");

        client_clear_all_local_ = this->create_client<std_srvs::srv::Trigger>(
        "/local_costmap/virtual_layer/clear_all");
    
        world_->setOnAddJenga([this](std::shared_ptr<Jenga> j) {
            this->add_jenga_to_virtual_layer(j);
        });
        world_->setOnRemoveJenga([this](std::string uuid) {
            this->remove_jenga_from_virtual_layer(uuid);
        });
        world_->setOnClearAllJengas([this]() {
            this->clear_all_jengas_from_virtual_layer();
        });
        return CallbackReturn::SUCCESS;
    }


    // Activation
    CallbackReturn on_activate(const rclcpp_lifecycle::State &) override {
        RCLCPP_INFO(get_logger(), "Activating and loading groups...");

        this->Lj = this->get_parameter("jenga_length").as_double();
        this->lj = this->get_parameter("jenga_width").as_double();

        auto wait = std::chrono::seconds(5);

        if (!client_add_global_->wait_for_service(wait) ||
            !client_remove_global_->wait_for_service(wait) ||
            !client_clear_all_global_->wait_for_service(wait) ||
            !client_add_local_->wait_for_service(wait) ||
            !client_remove_local_->wait_for_service(wait) ||
            !client_clear_all_local_->wait_for_service(wait))
        {
            RCLCPP_ERROR(get_logger(), "virtual_layer/add_polygon, virtual_layer/remove_shape or virtual_layer/clear_all services not available!");
            return CallbackReturn::FAILURE;
        }

        std::thread([this]() {
            auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
            
            // Envoi asynchrone de la demande de nettoyage
            client_clear_all_global_->async_send_request(request);
            client_clear_all_local_->async_send_request(request);
            
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
            
            RCLCPP_INFO(this->get_logger(), "Nettoyage terminé. Ajout des Jengas...");
            this->load_groups_from_params();
            RCLCPP_INFO(this->get_logger(), "Chargement initial terminé.");
        }).detach();
        
        return CallbackReturn::SUCCESS;
    }

    // Désactivation
    CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override {
        RCLCPP_INFO(get_logger(), "Deactivating...");
        this->world_->clearAllJengas();
        auto wait = std::chrono::seconds(5);
        client_add_global_.get()->wait_for_service(wait);
        client_remove_global_.get()->wait_for_service(wait);
        client_clear_all_global_.get()->wait_for_service(wait);
        client_add_local_.get()->wait_for_service(wait);
        client_remove_local_.get()->wait_for_service(wait);
        client_clear_all_local_.get()->wait_for_service(wait);
        return CallbackReturn::SUCCESS;
    }

private:

    rclcpp::Client<nav2_virtual_layer::srv::AddPolygon>::SharedPtr client_add_global_;
    rclcpp::Client<nav2_virtual_layer::srv::RemoveShape>::SharedPtr client_remove_global_;
    rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr client_clear_all_global_;
    rclcpp::Client<nav2_virtual_layer::srv::AddPolygon>::SharedPtr client_add_local_;
    rclcpp::Client<nav2_virtual_layer::srv::RemoveShape>::SharedPtr client_remove_local_;
    rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr client_clear_all_local_;

    std::unique_ptr<WorldState> world_; // Instance de ton gestionnaire d'état
    
    double Lj=0.15, lj=0.05; // Valeurs par défaut

    void load_groups_from_params() {
        auto parameters_and_prefixes = this->list_parameters({"groups"}, 10);
        std::set<std::string> group_names(parameters_and_prefixes.prefixes.begin(), parameters_and_prefixes.prefixes.end());
        
        std::set<std::string> processed_groups;

        for (const std::string & full_prefix : group_names) {
            try {
                double gx = this->get_parameter(full_prefix + ".x").as_double();
                double gy = this->get_parameter(full_prefix + ".y").as_double();
                std::string gtype_str = this->get_parameter(full_prefix + ".type").as_string();

                GroupType gtype = (gtype_str == "vertical") ? GroupType::VERTICAL : GroupType::HORIZONTAL;
                
                auto new_group = std::make_shared<JengaGroup>(full_prefix, gx, gy, gtype);
                new_group->createJengas(this->lj);

                world_->addGroup(new_group);
                std::this_thread::sleep_for(std::chrono::milliseconds(50));

            } catch (const std::exception & e) {
                RCLCPP_ERROR(get_logger(), "Error loading %s: %s", full_prefix.c_str(), e.what());
            }
        }
    }

    void add_jenga_to_virtual_layer(std::shared_ptr<Jenga> jenga) {
        if (!client_add_global_->service_is_ready() || !client_add_local_->service_is_ready()) {
            RCLCPP_ERROR(get_logger(), "Service AddPolygon not ready.");
            return;
        }
        if (!jenga || jenga->getOutline(this->Lj, this->lj).empty()) return;

        auto request = std::make_shared<nav2_virtual_layer::srv::AddPolygon::Request>();
        for (auto const& p : jenga->getOutline(this->Lj, this->lj)) {
            geometry_msgs::msg::Point ros_p;
            ros_p.x = p.x; ros_p.y = p.y; ros_p.z = 0.0;
            request->points.push_back(ros_p);
        }
        request->frame_id = "map";
        request->cost_level = 254;

        auto cb_global = [this, jenga](rclcpp::Client<nav2_virtual_layer::srv::AddPolygon>::SharedFuture future) {
            if (auto response = future.get(); response && response->success) {
                jenga->uuid_global = response->uuid;
                RCLCPP_INFO(get_logger(), "Jenga %s (Global) added.", jenga->id.c_str());
            } else {
                RCLCPP_ERROR(get_logger(), "Failed to add Jenga %s on global_costmap.", jenga->id.c_str());
            }
        };

        auto cb_local = [this, jenga](rclcpp::Client<nav2_virtual_layer::srv::AddPolygon>::SharedFuture future) {
            if (auto response = future.get(); response && response->success) {
                jenga->uuid_local = response->uuid;
                RCLCPP_INFO(get_logger(), "Jenga %s (Local) added.", jenga->id.c_str());
            } else {
                RCLCPP_ERROR(get_logger(), "Failed to add Jenga %s on local_costmap.", jenga->id.c_str());
            }
        };
        client_add_global_->async_send_request(request, cb_global);
        client_add_local_->async_send_request(request, cb_local);
    }

    void remove_jenga_from_virtual_layer(std::string uuid) {
        if (uuid.empty() || !client_remove_global_->service_is_ready()) return;

        auto request = std::make_shared<nav2_virtual_layer::srv::RemoveShape::Request>();
        request->identifier = uuid;

        auto future = client_remove_global_->async_send_request(request);
        auto status = future.wait_for(std::chrono::seconds(1));

        if (status == std::future_status::ready) {
            auto response = future.get();
            if (response && response->success) {
                RCLCPP_INFO(get_logger(), "Jenga %s removed.", uuid.c_str());
            } else {
                RCLCPP_ERROR(get_logger(), "Failed to remove Jenga %s.", uuid.c_str());
            }
        } else {
            RCLCPP_ERROR(get_logger(), "Timeout removing Jenga %s.", uuid.c_str());
        }
    }

    void clear_all_jengas_from_virtual_layer() {
        if (!client_clear_all_global_->service_is_ready() || !client_clear_all_local_->service_is_ready()) return;

        auto request = std::make_shared<std_srvs::srv::Trigger::Request>();
        
        // FIRE AND FORGET : Pour éviter les timeout liés à l'occupation du mutex côté serveur
        // (Surtout critique lors de la transition on_deactivate)
        client_clear_all_global_->async_send_request(request);
        client_clear_all_local_->async_send_request(request);
        
        RCLCPP_INFO(get_logger(), "Clear all request sent to Nav2.");
    }
};


int main(int argc, char **argv) {
    rclcpp::init(argc, argv);

    auto node = std::make_shared<JengaManager>();

    rclcpp::executors::MultiThreadedExecutor executor;
    executor.add_node(node->get_node_base_interface());

    executor.spin();
    rclcpp::shutdown();
    return 0;
}