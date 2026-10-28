import http from "node:http";
import { handle } from "./routes.js";

const ROWS = [{ name: "Blue Widget", price: 9.5 }, { name: "Red Gadget", price: 12 }];

http
  .createServer((req, res) => {
    const url = new URL(req.url, "http://localhost");
    const out = handle(`${req.method} ${url.pathname}`, ROWS, url.searchParams.get("name"));
    res.writeHead(out.status).end(out.body);
  })
  .listen(process.env.PORT ?? 3000);
