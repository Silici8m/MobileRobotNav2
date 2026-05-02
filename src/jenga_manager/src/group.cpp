#include "jenga_manager/group.hpp"
#include <cmath>
#include <vector>

/**
 * Constructeur de la classe JengaGroup
 */
JengaGroup::JengaGroup(std::string name, double x, double y, GroupType type)
    : name(name), x(x), y(y), type(type){
}

void JengaGroup::createJengas(double lj) {
        
    this->members.clear();
    
    std::vector<double> offsets = {
        -1.5 * lj, 
        -0.5 * lj, 
         0.5 * lj, 
         1.5 * lj
    };

    for (size_t i = 0; i < 4; i++)
    {
        std::string jenga_name = this->name + std::to_string(i);
        double j_x, j_y, j_theta;

        if (this->type == GroupType::HORIZONTAL) {
            j_x = this->x;
            j_y = this->y + offsets[i];
            j_theta = 0.0; 
        } 
        else { // VERTICAL
            j_x = this->x + offsets[i];
            j_y = this->y;
            j_theta = M_PI / 2.0;
        }
        this->members.push_back(std::make_shared<Jenga>(jenga_name, j_x, j_y, j_theta, ""));
    }
}

