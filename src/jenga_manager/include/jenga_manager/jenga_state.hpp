#ifndef JENGA_STATE_HPP
#define JENGA_STATE_HPP

#include "group.hpp"
#include "jenga.hpp"
#include <map>
#include <functional>

class WorldState {
public:
    using AddCallback = std::function<void(std::shared_ptr<Jenga>)>;
    using RemoveCallback = std::function<void(std::string uuid)>;
    using ClearAllCallback = std::function<void()>;

    void setOnAddJenga(AddCallback cb) { on_add_jenga_ = cb; }
    void setOnRemoveJenga(RemoveCallback cb) { on_remove_jenga_ = cb; }    
    void setOnClearAllJengas(ClearAllCallback cb) { on_clear_all_jengas_ = cb; }    

    std::shared_ptr<Jenga> getJenga(std::string id);
    void addJenga(std::shared_ptr<Jenga> jenga);
    void addGroup(std::shared_ptr<JengaGroup> group);
    std::shared_ptr<Jenga> findNearest(double x, double y);
    void removeJenga(std::string id);
    bool exist(std::string id);
    void clearAllJengas();

private:
    // Store all Jenga blocks by ID for fast access
    std::map<std::string, std::shared_ptr<Jenga>> all_jengas_;
    AddCallback on_add_jenga_;
    RemoveCallback on_remove_jenga_;
    ClearAllCallback on_clear_all_jengas_;
};

#endif // JENGA_STATE_HPP