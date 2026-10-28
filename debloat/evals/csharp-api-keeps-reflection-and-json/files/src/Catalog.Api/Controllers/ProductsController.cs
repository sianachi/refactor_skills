using Catalog.Api.Models;
using Catalog.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Catalog.Api.Controllers;

[ApiController]
[Route("products")]
public class ProductsController : ControllerBase
{
    private readonly IProductService _service;

    public ProductsController(IProductService service)
    {
        _service = service;
    }

    [HttpGet]
    public async Task<IActionResult> List([FromQuery] int page = 1, [FromQuery] int pageSize = 10)
    {
        var result = await _service.ListAsync(page, pageSize);
        return Ok(result);
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> Get(int id)
    {
        var result = await _service.GetAsync(id);
        if (!result.Success)
        {
            return NotFound();
        }

        return Ok(result.Value);
    }

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] CreateProductRequest request)
    {
        var result = await _service.CreateAsync(request);
        if (!result.Success)
        {
            return BadRequest(new { error = result.Error });
        }

        return Created("/products/" + result.Value!.Id, result.Value);
    }

    [HttpGet("{id:int}/price")]
    public async Task<IActionResult> Price(int id, [FromQuery] int qty = 1)
    {
        var result = await _service.QuoteAsync(id, qty);
        if (!result.Success)
        {
            if (result.Error == "not found")
            {
                return NotFound();
            }

            return BadRequest(new { error = result.Error });
        }

        return Ok(result.Value);
    }
}
