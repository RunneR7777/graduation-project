<template>
    <!-- 地址列 -->
    <template v-slot:item.address="{ item }">
        <v-btn
            text
            color="primary"
            @click="navigateToAddressAnalysis(item.address)"
        >
            {{ item.address }}
        </v-btn>
    </template>
</template>

<script>
export default {
    methods: {
        navigateToAddressAnalysis(address) {
            try {
                // 对IPv6地址进行编码以避免URL解析问题
                const encodedAddress = encodeURIComponent(address);
                this.$router.push(`/ipv6/address/${encodedAddress}`).catch(err => {
                    if (err.name !== 'NavigationDuplicated') {
                        console.error('导航错误:', err);
                        this.$message.error('页面导航失败');
                    }
                });
            } catch (error) {
                console.error('导航方法错误:', error);
                this.$message.error('页面导航失败');
            }
        },
    },
};
</script>