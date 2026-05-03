#include "jenga_manager/jenga.hpp"
#include <cmath>
#include <vector>

/**
 * Constructeur de la classe Jenga
 */
Jenga::Jenga(std::string id, double x, double y, double theta, std::string color)
    : id(id), x(x), y(y), theta(theta), color(color) {
    // L'UUID sera assigné plus tard par le service Nav2
    this->uuid_global = ""; 
    this->uuid_local = ""; 
}

/**
 * Calcule les 4 coins du rectangle pour Nav2
 * Utilise les dimensions Lj = 0.15m et lj = 0.05m
 */
std::vector<Point> Jenga::getOutline(double Lj, double lj) {
    std::vector<Point> corners;

    // Définition des demi-dimensions
    double half_L = Lj / 2.0;
    double half_l = lj / 2.0;

    // Les 4 combinaisons de signes pour les coins (+/+, +/-, -/-, -/+)
    double dx_offsets[] = {half_L, half_L, -half_L, -half_L};
    double dy_offsets[] = {half_l, -half_l, -half_l, half_l};

    for (int i = 0; i < 4; ++i) {
        Point p;
        // Formule de rotation 2D :
        // x' = x + (dx * cos(theta) - dy * sin(theta))
        // y' = y + (dx * sin(theta) + dy * cos(theta))
        p.x = x + (dx_offsets[i] * std::cos(theta) - dy_offsets[i] * std::sin(theta));
        p.y = y + (dx_offsets[i] * std::sin(theta) + dy_offsets[i] * std::cos(theta));
        
        corners.push_back(p);
    }

    return corners;
}

