new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        namespace_id: '',
        groups: [],
        selectedGroup: '',
        searchDataId: '',
        paginatedConfigs: [],  // 存储当前分页显示的数据
        currentPage: 1,
        pageSize: 10,
        totalPages: 1,
        totalCount: 0,  // 总记录数
        loadingGroups: false,
        loadingConfigs: false,
        showModal: false,
        isEditing: false,
        isViewing: false,
        newConfig: {
            group: '',
            dataId: '',
            content: '',
            desc: '',
            type: 'yaml'
        }
    },
    created() {
        this.namespace_id = window.location.pathname.split('/')[2];
        this.fetchGroups();
    },
    methods: {
        fetchGroups() {
            this.loadingGroups = true;
            fetch(`/api/namespaces/${this.namespace_id}/groups`)
                .then(response => response.json())
                .then(data => {
                    this.groups = data;
                    this.loadingGroups = false;
                })
                .catch(error => {
                    console.error('Error fetching groups:', error);
                    this.loadingGroups = false;
                });
        },
        fetchConfigs() {
            if (!this.selectedGroup) {
                console.log('未选择组，不进行请求。');
                return;
            }

            this.loadingConfigs = true;
            const params = new URLSearchParams({
                dataId: this.searchDataId || '',
                pageNo: this.currentPage,
                pageSize: this.pageSize
            });

            fetch(`/api/namespaces/${this.namespace_id}/groups/${this.selectedGroup}/data_ids?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    this.paginatedConfigs = data.pageItems || [];
                    this.totalCount = data.totalCount || 0;
                    this.totalPages = data.pagesAvailable || 1;
                    this.loadingConfigs = false;
                })
                .catch(error => {
                    console.error('Error fetching data IDs:', error);
                    this.loadingConfigs = false;
                });
        },
        onGroupChange() {
            this.currentPage = 1;
            this.searchConfigs();
        },
        searchConfigs() {
            this.currentPage = 1;
            this.fetchConfigs();
        },
        changePage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
                this.fetchConfigs();
            }
        },
        viewDetails(config) {
            this.isViewing = true;
            this.isEditing = false;
            fetch(`/api/namespaces/${this.namespace_id}/groups/${config.group}/data_ids/${config.dataId}`)
                .then(response => response.json())
                .then(data => {
                    this.newConfig = { ...data };
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('Error fetching config details:', error);
                    alert('获取配置详情失败');
                });
        },
        editConfig(config) {
            this.isViewing = false;
            this.isEditing = true;
            fetch(`/api/namespaces/${this.namespace_id}/groups/${config.group}/data_ids/${config.dataId}`)
                .then(response => response.json())
                .then(data => {
                    this.newConfig = { ...data };
                    this.showModal = true;
                })
                .catch(error => {
                    console.error('Error fetching config details:', error);
                    alert('获取配置详情失败');
                });
        },
        openCreateModal() {
            this.isViewing = false;
            this.isEditing = false;
            this.newConfig = { group: this.selectedGroup, dataId: '', content: '', desc: '', type: 'yaml' };
            this.showModal = true;
        },
        closeCreateModal() {
            this.showModal = false;
        },
        submitConfig() {
            if (!this.newConfig.group || !this.newConfig.dataId) {
                alert('请填写组和数据 ID');
                return;
            }

            const url = `/api/namespaces/${this.namespace_id}/groups/${this.newConfig.group}/data_ids/${this.newConfig.dataId}`;
            const method = this.isEditing ? 'PUT' : 'POST';

            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: this.newConfig.content,
                    desc: this.newConfig.desc,
                    type: this.newConfig.type
                })
            })
            .then(response => response.json())
            .then(data => {
                alert('配置提交成功');
                this.closeCreateModal();
                this.fetchConfigs();
            })
            .catch(error => {
                console.error('Error submitting config:', error);
                alert('配置提交失败');
            });
        },
        paginationRange() {
            const range = [];
            const delta = 2;  // 中间页面的数量
            const left = Math.max(2, this.currentPage - delta);
            const right = Math.min(this.totalPages - 1, this.currentPage + delta);

            range.push(1);  // Always show the first page

            if (left > 2) {
                range.push('...');
            }

            for (let i = left; i <= right; i++) {
                range.push(i);
            }

            if (right < this.totalPages - 1) {
                range.push('...');
            }

            if (this.totalPages > 1) {
                range.push(this.totalPages);  // Always show the last page
            }

            return range;
        },
        goBack() {
            window.location.href = '/namespace';
        }
    }
});
