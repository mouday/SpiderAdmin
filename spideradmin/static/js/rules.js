var rules = {
  data() {
    return {
      rules: {
        server_name: [
          { required: true, message: "请输入服务器名称", trigger: "blur" },
        ],
        server_host: [
          { required: true, message: "请输入服务器地址", trigger: "blur" },
        ],
        project_name: [
          { required: true, message: "请输入项目名称", trigger: "blur" },
        ],
        spider_name: [
          { required: true, message: "请输入爬虫名称", trigger: "blur" },
        ],
      },
    };
  },
};
