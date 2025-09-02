package com.project.productmanagement.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.project.productmanagement.entity.Product;

public interface ProductRepository extends JpaRepository<Product, Long> {

}
