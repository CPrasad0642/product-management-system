package com.project.productmanagement.service.impl;

import java.util.List;

import org.springframework.stereotype.Service;

import com.project.productmanagement.entity.Product;
import com.project.productmanagement.exception.ResourceNotFoundException;
import com.project.productmanagement.repository.ProductRepository;
import com.project.productmanagement.service.ProductService;

import jakarta.transaction.Transactional;


@Service
@Transactional
public class ProductServiceImpl implements ProductService {
	
	private final ProductRepository productRepository;
	
	public ProductServiceImpl(ProductRepository productRepository)
	{
		this.productRepository=productRepository;
	}
	@Override
	public Product addProduct(Product product) {
		product.setId(null);
		return productRepository.save(product);
	}

}
