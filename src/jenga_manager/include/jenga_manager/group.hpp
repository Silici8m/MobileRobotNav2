#ifndef GROUP_HPP
#define GROUP_HPP

#include "jenga.hpp"
#include <memory>
#include <vector>
#include <string>

enum class GroupType { HORIZONTAL, VERTICAL };

class JengaGroup {
public:
    JengaGroup(std::string name, double x, double y, GroupType type);
            
    // Calcule et crée les 4 objets Jenga du groupe
    void createJengas(double lj);

    std::string name;
    double x, y;
    GroupType type;
    std::vector<std::shared_ptr<Jenga>> members;
};

#endif