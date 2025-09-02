package com.project.productmanagement.controller;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.project.productmanagement.entity.Product;
import com.project.productmanagement.service.ProductService;

@RestController
@RequestMapping("/product")
public class ProductController {
	
	private final ProductService service;
	
	public ProductController(ProductService service)
	{
		this.service=service;
	}
	@PostMapping
	@ResponseStatus(HttpStatus.CREATED)
	public Product create(@RequestBody Product product)
	{
		return service.addProduct(product);
	}

}
