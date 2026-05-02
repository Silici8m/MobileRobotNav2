#ifndef JENGA_HPP
#define JENGA_HPP

#include <string>
#include <vector>
#include <string>
#include <vector>

struct Point { double x, y; };

class Jenga {
public:
    Jenga(std::string id, double x, double y, double theta, std::string color);
    
    // Retourne les 4 coins pour le polygone Nav2
    std::vector<Point> getOutline(double Lj, double lj);
    
    std::string id;
    std::string uuid;
    double x, y, theta;
    std::string color;
};

#endif